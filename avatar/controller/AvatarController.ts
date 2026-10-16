import * as THREE from 'three';
// @ts-ignore - Three.js exact path export mismatch in this bundler configuration
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
import { CanonicalBones, validateBoneMap } from './boneMap';
import { AvatarCapabilities, createEmptyCapabilities } from './avatarCapabilities';
import { HandController } from './HandController';
import { AnatomicalAnchors } from './AnatomicalAnchors';
import { ArmIKController } from './ArmIKController';

export type AnimationMode = string;

export class AvatarController {
  public rootScene: THREE.Group | null = null;
  public skeleton: THREE.Skeleton | null = null;
  public animationClips: THREE.AnimationClip[] = [];
  public capabilities: AvatarCapabilities = createEmptyCapabilities();
  public boneMapCache: Map<string, THREE.Bone> = new Map();
  
  public anchors: AnatomicalAnchors | null = null;
  public armIK: { left: ArmIKController | null; right: ArmIKController | null } = { left: null, right: null };
  public hands: { left: HandController | null; right: HandController | null } = { left: null, right: null };

  public mixer: THREE.AnimationMixer | null = null;
  public animationMode: AnimationMode = "manual";

  constructor() {}

  public async loadGLB(url: string): Promise<void> {
    const loader = new GLTFLoader();
    
    return new Promise((resolve, reject) => {
      loader.load(
        url,
        (gltf: any) => {
          this.rootScene = gltf.scene;
          this.animationClips = gltf.animations || [];
          
          let foundSkeleton: THREE.Skeleton | null = null;
          let boneCount = 0;
          let meshCount = 0;
          let hasMorphTargets = false;

          const bonesList: THREE.Bone[] = [];
          if (!this.rootScene) return;

          this.rootScene.traverse((child: THREE.Object3D) => {
            if ((child as THREE.Bone).isBone) {
               boneCount++;
               bonesList.push(child as THREE.Bone);
            }
            if ((child as THREE.SkinnedMesh).isSkinnedMesh) {
              meshCount++;
              if ((child as THREE.SkinnedMesh).skeleton && !foundSkeleton) {
                 foundSkeleton = (child as THREE.SkinnedMesh).skeleton;
              }
              if ((child as THREE.SkinnedMesh).morphTargetDictionary) {
                 hasMorphTargets = true;
              }
            } else if ((child as THREE.Mesh).isMesh) {
              meshCount++;
            }
          });

          // Even if skeleton object isn't directly bound in one mesh, we can collect bones
          if (!foundSkeleton && bonesList.length > 0) {
             foundSkeleton = new THREE.Skeleton(bonesList);
          }

          this.skeleton = foundSkeleton;
          this.buildBoneMapCache();
          
          this.calculateCapabilities(boneCount, meshCount, hasMorphTargets);

          // Initialize independent controller abstractions safely
          this.anchors = new AnatomicalAnchors(this);
          this.armIK.left = new ArmIKController('left', this);
          this.armIK.right = new ArmIKController('right', this);
          
          this.hands.left = new HandController('left', this);
          this.hands.right = new HandController('right', this);
          
          this.mixer = new THREE.AnimationMixer(this.rootScene);
          this.attachMixerEvents();

          resolve();
        },
        undefined,
        (error: any) => {
          console.error("AvatarController Error:", error);
          reject(error);
        }
      );
    });
  }

  private buildBoneMapCache() {
    if (!this.rootScene) return;
    this.boneMapCache.clear();
    
    this.rootScene.traverse((child: THREE.Object3D) => {
      if ((child as THREE.Bone).isBone) {
        const sanitizedChildName = child.name.replace(/[:_]/g, '');
        for (const [canonical, mixamo] of Object.entries(CanonicalBones)) {
          const sanitizedMixamo = mixamo.replace(/[:_]/g, '');
          if (sanitizedChildName === sanitizedMixamo) {
             this.boneMapCache.set(canonical, child as THREE.Bone);
          }
        }
      }
    });
  }

  private calculateCapabilities(boneCount: number, meshCount: number, hasMorphTargets: boolean) {
    if (!this.rootScene) return;

    const validation = validateBoneMap(this.rootScene);

    const caps = createEmptyCapabilities();
    caps.boneCount = boneCount;
    caps.meshCount = meshCount;
    caps.animationCount = this.animationClips.length;

    if (this.skeleton && boneCount > 0) {
      caps.hasSkeleton = true;
      caps.hasAnimationClips = this.animationClips.length > 0;
      caps.hasFaceMorphTargets = hasMorphTargets;

      // Extract specific capabilities
      caps.hasHips = !validation.missingRequired.includes("Hips");
      caps.hasSpine = !validation.missingRequired.includes("Spine");
      caps.hasHead = !validation.missingRequired.includes("Head");
      caps.hasHeadBone = caps.hasHead;

      caps.hasLeftArm = !validation.missingRequired.includes("LeftArm");
      caps.hasRightArm = !validation.missingRequired.includes("RightArm");
      caps.hasLeftHand = !validation.missingRequired.includes("LeftHand");
      caps.hasRightHand = !validation.missingRequired.includes("RightHand");

      const leftFingers = [
        "LeftHandThumb1", "LeftHandIndex1", "LeftHandMiddle1", "LeftHandRing1", "LeftHandPinky1"
      ];
      caps.hasLeftFingers = leftFingers.every(f => !validation.missingRequired.includes(f));

      const rightFingers = [
        "RightHandThumb1", "RightHandIndex1", "RightHandMiddle1", "RightHandRing1", "RightHandPinky1"
      ];
      caps.hasRightFingers = rightFingers.every(f => !validation.missingRequired.includes(f));
      
      // Structural vs Signing
      caps.isStructuralValid = caps.hasSkeleton && caps.boneCount > 10; 
      caps.isSigningValid = validation.isValid; // isValid means 0 missing required bones
    }
    this.capabilities = caps;
  }

  // Debugging utility to map all hierarchy and print
  public getHierarchyReport(): string {
    if (!this.rootScene) return "No scene loaded";
    let output = "--- ACTUAL GLB HIERARCHY ---\n";
    this.rootScene.traverse((child: import("three").Object3D) => {
        if ((child as import("three").Bone).isBone) {
           const parent = child.parent ? child.parent.name : "ROOT";
           const children = child.children.map(c => c.name).join(", ");
           output += `Bone: ${child.name} | Parent: ${parent} | Children: [${children}]\n`;
        }
    });
    return output;
  }

  public getNeutralClip(): THREE.AnimationClip | undefined {
     return this.animationClips.find(c => c.name === 'ASL_NEUTRAL' || c.name === 'mixamo.com' || c.name === 'neutral') || (this.animationClips.length > 0 ? this.animationClips[0] : undefined);
  }

  public getActiveAction(): THREE.AnimationAction | null {
     if (!this.mixer || (!this.animationMode.startsWith('clip:') && this.animationMode !== 'generic')) return null;
     const clipName = this.animationMode.startsWith('clip:') ? this.animationMode.split(':')[1] : (this.animationClips.length > 0 ? this.animationClips[0].name : null);
     if (!clipName) return null;
     let clip = this.animationClips.find(c => c.name === clipName);
     if (!clip && (clipName === 'ASL_NEUTRAL' || clipName === 'NEUTRAL')) {
        clip = this.getNeutralClip();
     }
     if (clip) return this.mixer.clipAction(clip);
     return null;
  }

  private attachMixerEvents() {
     if (!this.mixer) return;
     this.mixer.addEventListener('finished', (e: any) => {
         const finishedClip = e.action.getClip().name;
         if (finishedClip !== 'ASL_NEUTRAL' && finishedClip !== 'mixamo.com') {
             // Return to neutral smoothly resolving any residual clip bounds cleanly
             const neutralClip = this.getNeutralClip();
             if (neutralClip) {
                 const neutralAction = this.mixer!.clipAction(neutralClip);
                 neutralAction.reset();
                 neutralAction.setLoop(THREE.LoopRepeat, Infinity);
                 neutralAction.clampWhenFinished = false;
                 
                 e.action.fadeOut(0.4);
                 neutralAction.fadeIn(0.4).play();
                 
                 this.animationMode = "clip:ASL_NEUTRAL";
                 if (this.rootScene) this.rootScene.userData.currentAction = neutralAction;
             }
         }
     });
  }

  public setMode(mode: string) {
     this.animationMode = mode as any;
     if (this.mixer) {
        if (mode === 'generic' && this.animationClips.length > 0) {
           this.mixer.stopAllAction();
           const action = this.mixer.clipAction(this.animationClips[0]);
           action.play();
        } else if (mode.startsWith('clip:')) {
           const clipName = mode.split(':')[1];
           let clip = this.animationClips.find(c => c.name === clipName);
           if (!clip && (clipName === 'ASL_NEUTRAL' || clipName === 'NEUTRAL')) {
              clip = this.getNeutralClip();
           }
           if (clip) {
               const action = this.mixer.clipAction(clip);
               action.reset();
               
               const isNeutral = (clipName === 'ASL_NEUTRAL' || clipName === 'NEUTRAL' || clip.name === 'mixamo.com');
               if (isNeutral) {
                   action.setLoop(THREE.LoopRepeat, Infinity);
                   action.clampWhenFinished = false;
               } else {
                   action.setLoop(THREE.LoopOnce, 1);
                   action.clampWhenFinished = true; // Enables 'finished' event explicitly! 
               }
               
               // Crossfade if overriding another active target!
               const currentActive = this.rootScene?.userData.currentAction;
               if (currentActive && currentActive !== action) {
                   currentActive.fadeOut(0.4);
                   action.reset().fadeIn(0.4).play();
               } else if (!currentActive) {
                   this.mixer.stopAllAction();
                   action.play();
               }
               if (this.rootScene) this.rootScene.userData.currentAction = action;
           }
        }
     }
  }

  /**
   * Route a recognition prediction label to its corresponding animation clip.
   * Label must match the canonical vocabulary name (e.g. "HELLO", "YES", "NO").
   * Falls back gracefully to ASL_NEUTRAL when the clip asset is absent.
   */
   public playSignByLabel(label: string): void {
      if (!label) return;
      const sanitizedLabel = label.toUpperCase().trim();
      const targetClipName = `ASL_${sanitizedLabel}`;
      const targetMode = `clip:${targetClipName}`;

      // Prevent redundant restarts if the same clip is currently playing
      const currentAction = this.rootScene?.userData.currentAction;
      if (this.animationMode === targetMode && currentAction && currentAction.isRunning()) {
         return;
      }

      const clipExists = this.animationClips.some(c => c.name === targetClipName);
      if (clipExists) {
         this.setMode(targetMode);
      } else {
         console.warn(
           `[AvatarController] Label "${sanitizedLabel}" recognised but no clip "${targetClipName}" found — returning to neutral.`
         );
         this.setMode('clip:ASL_NEUTRAL');
      }
   }

  public update(delta: number) {
     if (this.mixer && (this.animationMode === 'generic' || this.animationMode.startsWith('clip:'))) {
        // 1. Generic/background animation evaluates overriding all hierarchy joints globally
        this.mixer.update(delta);
        this.rootScene?.updateMatrixWorld(true);
     }
     
     // Only stomp the skeleton actively if we are NOT running an explicit ASL clip performance
     if (!this.animationMode.startsWith('clip:')) {
         // 3 & 4. Hand & Finger Sub-controllers apply localized quaternion structures
         // strictly overwriting generic outputs ensuring rigid body separation natively, establishing 
         // the explicit deterministic pointing orientation baseline natively securely.
         this.hands.left?.update();
         this.hands.right?.update();

         // 5 & 6. Evaluate and Apply Arbitrary Arm Inverse Kinematics explicitly targeting 
         // Shoulder->Elbow->Forearm joints deterministically. This explicitly overwrites Hand world direction cleanly 
         // dynamically adapting directly onto cleanly finalized Hand rotations dynamically.
         this.armIK.left?.update();
         this.armIK.right?.update();
     }
  }

  public getBone(canonicalName: string): THREE.Bone | undefined {
    return this.boneMapCache.get(canonicalName);
  }
}
