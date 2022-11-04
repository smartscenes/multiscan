//
//  CameraViewController.swift
//  ScannerApp-Swift
//
//  Created by Zheren Xiao on 2020-11-20.
//  Copyright © 2020 jx16. All rights reserved.
//

import ARKit
import RealityKit
import UIKit

enum RecordingMode {
    case singleCamera
    case dualCamera
    case arCamera
    case stereoDepth
}

protocol CameraViewControllerPopUpViewDelegate: class {
    func startRecording()
    func dismissPopUpView()
}

/// Manage the camera preview when using the App
class CameraViewController: UIViewController, CameraViewControllerPopUpViewDelegate {
    
    private let mode: RecordingMode
    
    private var recordingManager: RecordingManager! = nil
    
    private let popUpView: PopUpView = PopUpView()
    private let recordButton: UIButton = {
        let btn = UIButton(type: .system)
        btn.setTitle("Record", for: .normal)
        btn.setTitleColor(.white, for: .normal)
        btn.setTitleColor(.gray, for: .disabled)
        btn.backgroundColor = .systemBlue
        btn.addTarget(self, action: #selector(recordButtonTapped), for: .touchUpInside)
        return btn
    }()

    init(mode: RecordingMode) {
        self.mode = mode
        super.init(nibName: nil, bundle: nil)
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    /// Set up the camera preview activity
    override func viewDidLoad() {
        super.viewDidLoad()

        view.backgroundColor = .white
        
        initRecordingManagerAndPerformRecordingModeRelatedSetup()
        setupPopUpView()
        setupRecordButton()
        
        // dismiss keyboard when tap elsewhere
        let tap: UITapGestureRecognizer = UITapGestureRecognizer(
            target: self,
            action: #selector(dismissKeyboard))
        view.addGestureRecognizer(tap)
        
    }
    
    @objc private func dismissKeyboard() {
        view.endEditing(true)
    }
    
    /// Make sure the screen do not dim
    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        
        // The screen shouldn't dim during AR experiences.
        UIApplication.shared.isIdleTimerDisabled = true
    }
    
    /// initialize recording manager and recording mode related set up (Ex: fill options such as single camera, dual camera etc.)
    private func initRecordingManagerAndPerformRecordingModeRelatedSetup() {
        
        switch mode {
        case .singleCamera:
            
            recordingManager = SingleCameraRecordingManager()
            let previewView = PreviewView()
            previewView.videoPreviewLayer.session = recordingManager.getSession() as? AVCaptureSession
            
            setupPreviewView(previewView: previewView)
            navigationItem.title = "Single Camera"
        
        case .dualCamera:
            
            if #available(iOS 13.0, *) {
                
                recordingManager = DualCameraRecordingManager()
                let session = recordingManager.getSession() as! AVCaptureMultiCamSession
                
                // setup dual cam preview
                let primaryCameraPreviewView = PreviewView()
                primaryCameraPreviewView.videoPreviewLayer.setSessionWithNoConnection(session)
                
                let secondaryPreviewView = PreviewView()
                secondaryPreviewView.videoPreviewLayer.setSessionWithNoConnection(session)
                
                // primary camera preview
                let primaryCameraInput = session.inputs[0] as! AVCaptureDeviceInput
                guard let primaryCameraPort = primaryCameraInput.ports(for: .video,
                                                                 sourceDeviceType: .builtInWideAngleCamera,
                                                                 sourceDevicePosition: primaryCameraInput.device.position).first
                else {
                    print("Could not obtain wide angle camera input ports")
                    return
                }
                let primaryCameraPreviewLayerConnection = AVCaptureConnection(inputPort: primaryCameraPort, videoPreviewLayer: primaryCameraPreviewView.videoPreviewLayer)
                guard session.canAddConnection(primaryCameraPreviewLayerConnection) else {
                    print("Could not add a connection to the wide-angle camera video preview layer")
                    return
                }
                session.addConnection(primaryCameraPreviewLayerConnection)
                
                // secondary camera preview
                let secondaryCameraInput = session.inputs[1] as! AVCaptureDeviceInput
                
                var secondaryCameraPort: AVCaptureInput.Port
                
                if secondaryCameraInput.device.deviceType == .builtInUltraWideCamera {
                    secondaryCameraPort = secondaryCameraInput.ports(for: .video,
                                                                     sourceDeviceType: .builtInUltraWideCamera,
                                                                     sourceDevicePosition: secondaryCameraInput.device.position).first!
                } else if secondaryCameraInput.device.deviceType == .builtInTelephotoCamera {
                    secondaryCameraPort = secondaryCameraInput.ports(for: .video,
                                                                     sourceDeviceType: .builtInTelephotoCamera,
                                                                     sourceDevicePosition: secondaryCameraInput.device.position).first!
                } else {
                    print("Could not obtain secondary camera input ports")
                    return
                }
                
                let secondaryCameraPreviewLayerConnection = AVCaptureConnection(inputPort: secondaryCameraPort, videoPreviewLayer: secondaryPreviewView.videoPreviewLayer)
                guard session.canAddConnection(secondaryCameraPreviewLayerConnection) else {
                    print("Could not add a connection to the secondary camera video preview layer")
                    return
                }
                session.addConnection(secondaryCameraPreviewLayerConnection)
                
                setupDualPreview(pv1: primaryCameraPreviewView, pv2: secondaryPreviewView)
                
                navigationItem.title = "Dual Camera"
                
            } else {
                print("Dual camera mode only available for iOS 13.0 or newer.")
            }
        
        case .arCamera:
            
            if #available(iOS 14.0, *) {
                
                recordingManager = ARCameraRecordingManager()
                let session = recordingManager.getSession() as! ARSession
                let arView = ARView()
                arView.session = session
		arView.renderOptions = [.disablePersonOcclusion, .disableDepthOfField, .disableMotionBlur]
				
		arView.automaticallyConfigureSession = false
				
		arView.debugOptions.insert(.showSceneUnderstanding)
                
                setupPreviewView(previewView: arView)
                navigationItem.title = "Color Camera + LiDAR"
                
            } else {
                print("AR camera only available for iOS 14.0 or newer.")
            }

        case .stereoDepth:
            
            if #available(iOS 13.0, *) {
                recordingManager = StereoDepthRecordingManager()
                
                let previewView = PreviewView()
                previewView.videoPreviewLayer.session = recordingManager.getSession() as? AVCaptureSession
                
                setupPreviewView(previewView: previewView)
                navigationItem.title = "Stereo Depth"
                
            } else {
                print("Stereo depth only available for iOS 13.0 or newer.")
            }
            
        }
        
    }
    
    private func setupPreviewView(previewView: UIView) {
        
        view.addSubview(previewView)
        previewView.translatesAutoresizingMaskIntoConstraints = false
        previewView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor).isActive = true
        previewView.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.bottomAnchor).isActive = true
        previewView.leftAnchor.constraint(equalTo: view.safeAreaLayoutGuide.leftAnchor).isActive = true
        previewView.rightAnchor.constraint(equalTo: view.safeAreaLayoutGuide.rightAnchor).isActive = true
    
    }
    
    private func setupDualPreview(pv1: UIView, pv2: UIView) {
        
        view.addSubview(pv1)
        pv1.translatesAutoresizingMaskIntoConstraints = false
        pv1.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor).isActive = true
        pv1.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.centerYAnchor).isActive = true
        pv1.leftAnchor.constraint(equalTo: view.safeAreaLayoutGuide.leftAnchor).isActive = true
        pv1.rightAnchor.constraint(equalTo: view.safeAreaLayoutGuide.rightAnchor).isActive = true
        
        view.addSubview(pv2)
        pv2.translatesAutoresizingMaskIntoConstraints = false
        pv2.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.centerYAnchor).isActive = true
        pv2.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.bottomAnchor).isActive = true
        pv2.leftAnchor.constraint(equalTo: view.safeAreaLayoutGuide.leftAnchor).isActive = true
        pv2.rightAnchor.constraint(equalTo: view.safeAreaLayoutGuide.rightAnchor).isActive = true
    
    }

    private func setupPopUpView() {
        
        popUpView.delegate = self
        
        view.addSubview(popUpView)
        
        popUpView.translatesAutoresizingMaskIntoConstraints = false
        popUpView.centerXAnchor.constraint(equalTo: view.centerXAnchor).isActive = true
        popUpView.centerYAnchor.constraint(equalTo: view.centerYAnchor).isActive = true
        
        DispatchQueue.main.async {
            self.popUpView.isHidden = true
        }
        
    }
    
    private func setupRecordButton() {
        
        view.addSubview(recordButton)
        recordButton.translatesAutoresizingMaskIntoConstraints = false
        recordButton.centerXAnchor.constraint(equalTo: view.safeAreaLayoutGuide.centerXAnchor).isActive = true
        recordButton.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.bottomAnchor, constant: -8).isActive = true
        
    }
    
    /// perform actions when user press the record button
    @objc func recordButtonTapped() {
        
        print("Record button tapped")
        
        if recordingManager.isRecording {
            stopRecording()
        } else {
            DispatchQueue.main.async {
                self.recordButton.isEnabled = false
                self.popUpView.isHidden = false
            }
        }
        
    }
    
    func startRecording() {
        
        DispatchQueue.main.async {
            self.popUpView.isHidden = true
            
            self.recordButton.setTitle("Stop", for: .normal)
            self.recordButton.backgroundColor = .systemRed
            self.recordButton.isEnabled = true
        }
        
        let username = popUpView.firstName + " " + popUpView.lastName
        let sceneDescription = popUpView.userInputDescription
        let sceneType = popUpView.sceneTypes[popUpView.sceneTypeIndex]
        recordingManager.startRecording(username: username, sceneDescription: sceneDescription, sceneType: sceneType)
        
    }
    
    func dismissPopUpView() {
        
        DispatchQueue.main.async {
            self.popUpView.isHidden = true
            self.recordButton.isEnabled = true
        }
        
    }
    
    func stopRecording() {
        
        recordingManager.stopRecording()

        DispatchQueue.main.async {
            self.recordButton.setTitle("Record", for: .normal)
            self.recordButton.backgroundColor = .systemBlue
        }
        
    }
    
}
