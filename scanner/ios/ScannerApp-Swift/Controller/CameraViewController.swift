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
}

protocol CameraViewControllerPopUpViewDelegate: class {
    func startRecording()
    func dismissPopUpView()
}

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
    
    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        
        // The screen shouldn't dim during AR experiences.
        UIApplication.shared.isIdleTimerDisabled = true
    }
    
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
                let mainCameraPreviewView = PreviewView()
                mainCameraPreviewView.videoPreviewLayer.setSessionWithNoConnection(session)
                
                let secondaryPreviewView = PreviewView()
                secondaryPreviewView.videoPreviewLayer.setSessionWithNoConnection(session)
                
                // TODO: tmp solution
                while session.inputs.count == 0 {
                    print("...")
                    usleep(1000)
                }
                
                // main camera preview
                let mainCameraInput = session.inputs[0] as! AVCaptureDeviceInput
                guard let mainCameraPort = mainCameraInput.ports(for: .video,
                                                                 sourceDeviceType: .builtInWideAngleCamera,
                                                                 sourceDevicePosition: mainCameraInput.device.position).first
                else {
                    print("Could not obtain wide angle camera input ports")
                    return
                }
                let mainCameraPreviewLayerConnection = AVCaptureConnection(inputPort: mainCameraPort, videoPreviewLayer: mainCameraPreviewView.videoPreviewLayer)
                guard session.canAddConnection(mainCameraPreviewLayerConnection) else {
                    print("Could not add a connection to the wide-angle camera video preview layer")
                    return
                }
                session.addConnection(mainCameraPreviewLayerConnection)
                
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
                
                setupDualPreview(pv1: mainCameraPreviewView, pv2: secondaryPreviewView)
                
                navigationItem.title = "Dual Camera"
                
            } else {
                // Fallback on earlier versions
            }
        
        case .arCamera:
            
            if #available(iOS 14.0, *) {
                
                recordingManager = ARCameraRecordingManager()
                let session = recordingManager.getSession() as! ARSession
                let arView = ARView()
                arView.session = session
                
                setupPreviewView(previewView: arView)
                navigationItem.title = "Color Camera + LiDAR"
                
            } else {
                print("AR camera only available for iOS 14.0 or newer.")
                // TODO: do something
            }
        
//        default:
//            print("Unexpected, this line of should be unreachable.")
//            // TODO: do something
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
