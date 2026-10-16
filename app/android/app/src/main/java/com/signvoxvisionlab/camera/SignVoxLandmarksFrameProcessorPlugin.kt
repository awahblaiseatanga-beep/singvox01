package com.signvoxvisionlab.camera

import android.content.Context
import com.google.mediapipe.framework.image.MediaImageBuilder
import com.google.mediapipe.tasks.core.BaseOptions
import com.google.mediapipe.tasks.vision.core.ImageProcessingOptions
import com.google.mediapipe.tasks.vision.core.RunningMode
import com.google.mediapipe.tasks.vision.facelandmarker.FaceLandmarker
import com.google.mediapipe.tasks.vision.handlandmarker.HandLandmarker
import com.google.mediapipe.tasks.vision.poselandmarker.PoseLandmarker
import com.mrousavy.camera.frameprocessors.Frame
import com.mrousavy.camera.frameprocessors.FrameProcessorPlugin
import com.mrousavy.camera.frameprocessors.VisionCameraProxy
import kotlin.math.max

/**
 * Reads VisionCamera's unmirrored back-camera ImageProxy and runs MediaPipe Tasks.
 * Rotation remains metadata until ImageProcessingOptions applies it during inference.
 * JS receives small status records per frame and the landmark arrays only on request.
 */
class SignVoxLandmarksFrameProcessorPlugin(
  proxy: VisionCameraProxy,
  @Suppress("UNUSED_PARAMETER") options: Map<String, Any>?,
) : FrameProcessorPlugin() {
  private val context: Context = proxy.context.applicationContext
  private var lastTimestampMs = 0L
  private var lastDiagnosticRequestId = 0L

  private val poseLandmarker = PoseLandmarker.createFromOptions(
    context,
    PoseLandmarker.PoseLandmarkerOptions.builder()
      .setBaseOptions(baseOptions("mediapipe_models/pose_landmarker.task"))
      .setRunningMode(RunningMode.VIDEO)
      .setNumPoses(1)
      .build(),
  )

  private val handLandmarker = HandLandmarker.createFromOptions(
    context,
    HandLandmarker.HandLandmarkerOptions.builder()
      .setBaseOptions(baseOptions("mediapipe_models/hand_landmarker.task"))
      .setRunningMode(RunningMode.VIDEO)
      .setNumHands(2)
      .build(),
  )

  private val faceLandmarker = FaceLandmarker.createFromOptions(
    context,
    FaceLandmarker.FaceLandmarkerOptions.builder()
      .setBaseOptions(baseOptions("mediapipe_models/face_landmarker.task"))
      .setRunningMode(RunningMode.VIDEO)
      .setNumFaces(1)
      .setOutputFaceBlendshapes(false)
      .setOutputFacialTransformationMatrixes(false)
      .build(),
  )

  override fun callback(frame: Frame, params: Map<String, Any>?): Any {
    val startNs = System.nanoTime()
    val imageProxy = frame.imageProxy
    val image = MediaImageBuilder(frame.image).build()
    try {
      val timestampMs = max(frame.timestamp / 1_000_000L, lastTimestampMs + 1L)
      lastTimestampMs = timestampMs
      val rotationDegrees = imageProxy.imageInfo.rotationDegrees
      val imageOptions = ImageProcessingOptions.builder()
        .setRotationDegrees(rotationDegrees)
        .build()

      val poseResult = poseLandmarker.detectForVideo(image, imageOptions, timestampMs)
      val handResult = handLandmarker.detectForVideo(image, imageOptions, timestampMs)
      val faceResult = faceLandmarker.detectForVideo(image, imageOptions, timestampMs)

      val rawLeftHand = zeros(21, 3)
      val rawRightHand = zeros(21, 3)
      var leftHandSeen = false
      var rightHandSeen = false
      var leftHandShapeValid = true
      var rightHandShapeValid = true
      handResult.landmarks().forEachIndexed { handIndex, landmarks ->
        val taskLabel = handResult.handedness()
          .getOrNull(handIndex)
          ?.firstOrNull()
          ?.categoryName()
        // MediaPipe's label convention assumes mirrored selfie input. These app frames
        // are from the unmirrored back camera, matching the canonical extractor's swap.
        val canonicalSide = when (taskLabel) {
          "Left" -> "Right"
          "Right" -> "Left"
          else -> null
        }
        val target = when (canonicalSide) {
          "Left" -> rawLeftHand
          "Right" -> rawRightHand
          else -> null
        }
        if (target != null) {
          if (landmarks.size == 21) {
            landmarks.forEachIndexed { pointIndex, point ->
              target[pointIndex] = listOf(point.x().toDouble(), point.y().toDouble(), point.z().toDouble())
            }
          } else if (canonicalSide == "Left") {
            leftHandShapeValid = false
          } else {
            rightHandShapeValid = false
          }
          if (canonicalSide == "Left") leftHandSeen = true
          if (canonicalSide == "Right") rightHandSeen = true
        }
      }

      val leftHand = validateGroup("leftHand", rawLeftHand, 21, 3, leftHandSeen, leftHandShapeValid)
      val rightHand = validateGroup("rightHand", rawRightHand, 21, 3, rightHandSeen, rightHandShapeValid)

      val rawPose = zeros(33, 5)
      val posePoints = poseResult.poseLandmarks().firstOrNull()
      val poseShapeValid = posePoints == null || posePoints.size == 33
      posePoints?.takeIf { it.size == 33 }?.forEachIndexed { index, point ->
        rawPose[index] = listOf(
          point.x().toDouble(),
          point.y().toDouble(),
          point.z().toDouble(),
          point.visibility().orElse(0.0f).toDouble(),
          point.presence().orElse(0.0f).toDouble(),
        )
      }
      val pose = validateGroup("pose", rawPose, 33, 5, posePoints != null, poseShapeValid)

      val rawFace = zeros(25, 3)
      val facePoints = faceResult.faceLandmarks().firstOrNull()
      val faceShapeValid = facePoints == null || facePoints.size >= 25
      facePoints?.takeIf { it.size >= 25 }?.take(25)?.forEachIndexed { index, point ->
        rawFace[index] = listOf(point.x().toDouble(), point.y().toDouble(), point.z().toDouble())
      }
      val face = validateGroup("face", rawFace, 25, 3, facePoints != null, faceShapeValid)

      val invalidGroups = listOf(leftHand, rightHand, pose, face)
        .filter { it.invalid }
        .map { it.name }
      val processingMs = (System.nanoTime() - startNs) / 1_000_000.0
      val result = mutableMapOf<String, Any>(
        "timestampMs" to timestampMs.toDouble(),
        "processingMs" to processingMs,
        "imageWidth" to imageProxy.width,
        "imageHeight" to imageProxy.height,
        "rotationDegrees" to rotationDegrees,
        "cameraFacing" to "back",
        "bufferMirrored" to false,
        "coordinateSpace" to "mediapipe-rotation-corrected-image-normalized",
        "groupStatus" to mapOf(
          "leftHand" to status(leftHand),
          "rightHand" to status(rightHand),
          "pose" to status(pose),
          "face" to status(face),
        ),
        "invalidGroups" to invalidGroups,
      )

      val requestedId = (params?.get("diagnosticRequestId") as? Number)?.toLong() ?: 0L
      if (requestedId > lastDiagnosticRequestId) {
        lastDiagnosticRequestId = requestedId
        result["diagnostic"] = mapOf(
          "requestId" to requestedId,
          "timestampMs" to timestampMs.toDouble(),
          "imageWidth" to imageProxy.width,
          "imageHeight" to imageProxy.height,
          "rotationDegrees" to rotationDegrees,
          "cameraFacing" to "back",
          "bufferMirrored" to false,
          "coordinateSpace" to "mediapipe-rotation-corrected-image-normalized",
          "groupStatus" to mapOf(
            "leftHand" to status(leftHand),
            "rightHand" to status(rightHand),
            "pose" to status(pose),
            "face" to status(face),
          ),
          "leftHand" to leftHand.points,
          "rightHand" to rightHand.points,
          "pose" to pose.points,
          "face" to face.points,
        )
      }
      return result
    } finally {
      image.close()
    }
  }

  private data class ValidatedGroup(
    val name: String,
    val points: List<List<Double>>,
    val detected: Boolean,
    val invalid: Boolean,
  )

  private fun validateGroup(
    name: String,
    points: List<List<Double>>,
    expectedPoints: Int,
    dimensions: Int,
    detected: Boolean,
    sourceShapeValid: Boolean = true,
  ): ValidatedGroup {
    val valid = sourceShapeValid && points.size == expectedPoints && points.all { point ->
      point.size == dimensions && point.all { value -> value.isFinite() }
    }
    if (!valid) {
      return ValidatedGroup(name, zeros(expectedPoints, dimensions), detected = false, invalid = true)
    }
    return ValidatedGroup(
      name,
      if (detected) points else zeros(expectedPoints, dimensions),
      detected = detected,
      invalid = false,
    )
  }

  private fun status(group: ValidatedGroup): String = if (group.detected) "detected" else "missing"

  private fun baseOptions(assetPath: String): BaseOptions =
    BaseOptions.builder().setModelAssetPath(assetPath).build()

  private fun zeros(rows: Int, columns: Int): MutableList<List<Double>> =
    MutableList(rows) { List(columns) { 0.0 } }
}
