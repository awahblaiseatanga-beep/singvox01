import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Platform,
  PermissionsAndroid,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import {
  Camera,
  runAtTargetFps,
  useCameraDevice,
  useFrameProcessor,
  VisionCameraProxy,
} from 'react-native-vision-camera';
import { runOnJS } from 'react-native-worklets-core';

type GroupName = 'leftHand' | 'rightHand' | 'pose' | 'face';
type GroupStatus = Record<GroupName, 'detected' | 'missing'>;
type Diagnostic = {
  requestId: number;
  timestampMs: number;
  imageWidth: number;
  imageHeight: number;
  rotationDegrees: number;
  cameraFacing: 'back';
  bufferMirrored: false;
  coordinateSpace: string;
  groupStatus: GroupStatus;
  leftHand: number[][];
  rightHand: number[][];
  pose: number[][];
  face: number[][];
};
type LandmarkStatusFrame = {
  timestampMs: number;
  processingMs: number;
  imageWidth: number;
  imageHeight: number;
  rotationDegrees: number;
  cameraFacing: 'back';
  bufferMirrored: false;
  coordinateSpace: string;
  groupStatus: GroupStatus;
  invalidGroups: GroupName[];
  diagnostic?: Diagnostic;
};

const landmarkPlugin = VisionCameraProxy.initFrameProcessorPlugin('signVoxLandmarks', {});

export default function App() {
  const [hasPermission, setHasPermission] = useState(false);
  const [isActive, setIsActive] = useState(false);
  const [landmarks, setLandmarks] = useState<LandmarkStatusFrame | null>(null);
  const [pipelineError, setPipelineError] = useState<string | null>(null);
  const [fps, setFps] = useState(0);
  const [frameCount, setFrameCount] = useState(0);
  const [diagnosticRequestId, setDiagnosticRequestId] = useState(0);
  const [diagnosticJson, setDiagnosticJson] = useState<string | null>(null);
  const previousFrameTimestamp = useRef<number | null>(null);
  const device = useCameraDevice('back');

  useEffect(() => {
    let mounted = true;
    const requestPermission = async () => {
      const status =
        Platform.OS === 'android'
          ? await PermissionsAndroid.request(PermissionsAndroid.PERMISSIONS.CAMERA)
          : await Camera.requestCameraPermission();
      if (mounted) {
        setHasPermission(
          Platform.OS === 'android'
            ? status === PermissionsAndroid.RESULTS.GRANTED
            : status === 'granted',
        );
      }
    };
    void requestPermission();
    return () => {
      mounted = false;
    };
  }, []);

  const onLandmarks = useCallback((frame: LandmarkStatusFrame) => {
    setPipelineError(null);
    const previousTimestamp = previousFrameTimestamp.current;
    if (previousTimestamp !== null && frame.timestampMs > previousTimestamp) {
      setFps(1000 / (frame.timestampMs - previousTimestamp));
    }
    previousFrameTimestamp.current = frame.timestampMs;
    setLandmarks(frame);
    setFrameCount((count) => count + 1);
    if (frame.invalidGroups.length > 0) {
      setPipelineError('Invalid landmark values were zero-filled: ' + frame.invalidGroups.join(', '));
    }
    if (frame.diagnostic) {
      setDiagnosticJson(JSON.stringify(frame.diagnostic, null, 2));
    }
  }, []);

  const onPipelineError = useCallback((message: string) => {
    setPipelineError(message);
  }, []);

  const frameProcessor = useFrameProcessor(
    (frame) => {
      'worklet';
      runAtTargetFps(8, () => {
        'worklet';
        if (landmarkPlugin == null) {
          runOnJS(onPipelineError)('Native MediaPipe frame processor is not registered.');
          return;
        }
        try {
          const result = landmarkPlugin.call(frame, { diagnosticRequestId }) as LandmarkStatusFrame;
          runOnJS(onLandmarks)(result);
        } catch (error) {
          runOnJS(onPipelineError)(String(error));
        }
      });
    },
    [diagnosticRequestId, onLandmarks, onPipelineError],
  );

  const groupStatus = landmarks?.groupStatus;
  const statusText = (group: GroupName) => groupStatus?.[group] ?? 'waiting';

  if (!hasPermission) return <Text style={styles.message}>Camera permission is required.</Text>;
  if (device == null) return <Text style={styles.message}>No back camera is available.</Text>;

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>SIGNVOX CAMERA</Text>
        <Text style={styles.status}>{isActive ? 'Camera active' : 'Camera stopped'}</Text>
      </View>

      <View style={styles.cameraContainer}>
        <Camera
          style={StyleSheet.absoluteFill}
          device={device}
          isActive={isActive}
          frameProcessor={frameProcessor}
          pixelFormat="yuv"
        />
      </View>

      <View style={styles.dashboard}>
        <Text style={styles.metricText}>Left hand: {statusText('leftHand')}</Text>
        <Text style={styles.metricText}>Right hand: {statusText('rightHand')}</Text>
        <Text style={styles.metricText}>Pose: {statusText('pose')}</Text>
        <Text style={styles.metricText}>Face: {statusText('face')}</Text>
        <Text style={styles.metricText}>Landmark processing: {landmarks ? landmarks.processingMs.toFixed(1) + ' ms' : '--'}</Text>
        <Text style={styles.metricText}>Measured processing rate: {fps ? fps.toFixed(1) + ' fps' : '--'}</Text>
        <Text style={styles.metricText}>
          Frame: {landmarks ? `${landmarks.imageWidth}×${landmarks.imageHeight}, rotate ${landmarks.rotationDegrees}°` : 'waiting'}
        </Text>
        <Text style={styles.metricText}>Processed frames: {frameCount}</Text>
        {pipelineError ? <Text style={styles.error}>{pipelineError}</Text> : null}

        <View style={styles.controls}>
          <TouchableOpacity style={styles.button} onPress={() => setIsActive(true)}>
            <Text style={styles.buttonText}>START CAMERA</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.button} onPress={() => setIsActive(false)}>
            <Text style={styles.buttonText}>STOP</Text>
          </TouchableOpacity>
        </View>
        <TouchableOpacity
          style={styles.diagnosticButton}
          onPress={() => {
            setDiagnosticJson(null);
            setDiagnosticRequestId((requestId) => requestId + 1);
          }}
        >
          <Text style={styles.buttonText}>CAPTURE ONE RAW LANDMARK FRAME</Text>
        </TouchableOpacity>
        {diagnosticJson ? (
          <ScrollView style={styles.diagnostic}>
            <Text selectable style={styles.diagnosticText}>{diagnosticJson}</Text>
          </ScrollView>
        ) : diagnosticRequestId > 0 ? (
          <Text style={styles.metricText}>Waiting for diagnostic frame {diagnosticRequestId}…</Text>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  header: { padding: 16, backgroundColor: '#111', alignItems: 'center' },
  title: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  status: { color: '#aaa', fontSize: 12, marginTop: 4 },
  cameraContainer: { flex: 1, overflow: 'hidden', backgroundColor: '#222' },
  dashboard: { padding: 12, backgroundColor: '#111' },
  metricText: { color: '#fff', fontFamily: 'monospace', fontSize: 11, marginBottom: 4 },
  error: { color: '#ff7777', fontSize: 12, marginTop: 6 },
  controls: { flexDirection: 'row', marginTop: 10, justifyContent: 'space-around' },
  button: { backgroundColor: '#333', padding: 12, borderRadius: 8, minWidth: '42%', alignItems: 'center' },
  diagnosticButton: { backgroundColor: '#145047', padding: 12, borderRadius: 8, marginTop: 8, alignItems: 'center' },
  buttonText: { color: '#fff', fontWeight: 'bold', fontSize: 12 },
  diagnostic: { maxHeight: 130, marginTop: 8, backgroundColor: '#080808', padding: 8 },
  diagnosticText: { color: '#a7e7cf', fontFamily: 'monospace', fontSize: 9 },
  message: { flex: 1, textAlign: 'center', textAlignVertical: 'center', backgroundColor: '#000', color: '#fff' },
});
