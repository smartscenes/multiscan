//
//  ViewController.swift
//  ScannerApp-Swift
//
//  Created by Zheren Xiao on 2019-12-20.
//  Copyright © 2019 jx16. All rights reserved.
//

import UIKit
import ARKit
import AVFoundation

/// View controller for the main activity
class ViewController: UIViewController {

    let recordingModes: [RecordingMode] = [.singleCamera, .dualCamera, .arCamera, .stereoDepth]
    var selectedRecordingMode: RecordingMode? = nil
    
    @IBOutlet weak var selectModeButton: UIButton!
    @IBOutlet weak var recordingModeTableView: UITableView!
    
    @IBOutlet weak var openCameraButton: UIButton!
    
    /// load components for the main activity
    override func viewDidLoad() {
        super.viewDidLoad()

        recordingModeTableView.delegate = self
        recordingModeTableView.dataSource = self
        
        recordingModeTableView.isHidden = true
        
        openCameraButton.isEnabled = false
    
    }
    
    @IBAction func selectModeButtonTapped(_ sender: Any) {
        UIView.animate(withDuration: 0.3) {
            self.recordingModeTableView.isHidden = !self.recordingModeTableView.isHidden
        }
//        selectModeButton.isEnabled = false
    }
    
    @IBAction func openCameraButtonTapped(_ sender: Any) {
        
        if let recordingMode = selectedRecordingMode {
            segueToCameraScene(mode: recordingMode)
        } else {
            print("Recording mode is not specified.")
        }
        
    }

    private func segueToCameraScene(mode: RecordingMode) {
        
        let vc = CameraViewController(mode: mode)
        vc.modalPresentationStyle = .fullScreen
        navigationController?.pushViewController(vc, animated: true)
        
    }
    
    private func isDualCameraModeSupported() -> Bool {
        if #available(iOS 13.0, *), AVCaptureMultiCamSession.isMultiCamSupported {
            return true
        } else {
            return false
        }
    }
    
    private func isARCameraModeSupported() -> Bool {
        if #available(iOS 14.0, *), ARWorldTrackingConfiguration.supportsFrameSemantics(.sceneDepth) {
            return true
        } else {
            return false
        }
    }
    
    private func isStereoDepthSupported() -> Bool {
        
        if #available(iOS 13.0, *) {
            let discoverySession = AVCaptureDevice.DiscoverySession(deviceTypes: [.builtInDualCamera, .builtInDualWideCamera], mediaType: .depthData, position: .back)
            
            return !discoverySession.devices.isEmpty 
            
        } else {
            return false
        }

    }

}

extension ViewController: UITableViewDelegate, UITableViewDataSource {
    
    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return recordingModes.count
    }
    
    /// table view for mode selections (Ex: Single camera)
    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = tableView.dequeueReusableCell(withIdentifier: "recordingModeCell", for: indexPath)

        switch recordingModes[indexPath.row] {
        case .singleCamera:
            cell.textLabel?.text = "Single Camera"
        
        case .dualCamera:
            if isDualCameraModeSupported() {
                cell.textLabel?.text = "Dual Camera"
            } else {
                cell.textLabel?.text = "Dual Camera (Not Available)"
                cell.isUserInteractionEnabled = false
                cell.textLabel?.textColor = .gray
            }
            
        case .arCamera:
            if isARCameraModeSupported() {
                cell.textLabel?.text = "LiDAR Depth"
            } else {
                cell.textLabel?.text = "LiDAR Depth (Not Available)"
                cell.isUserInteractionEnabled = false
                cell.textLabel?.textColor = .gray
            }
        
        case .stereoDepth:
            if isStereoDepthSupported() {
                cell.textLabel?.text = "Stereo Depth"
            } else {
                cell.textLabel?.text = "Stereo Depth (Not Available)"
                cell.isUserInteractionEnabled = false
                cell.textLabel?.textColor = .gray
            }
            
        default:
            cell.textLabel?.text = "Unknown Mode"
            cell.isUserInteractionEnabled = false
            cell.textLabel?.textColor = .gray
        }
        
        return cell
    }
    
    func tableView(_ tableView: UITableView, heightForRowAt indexPath: IndexPath) -> CGFloat {
        return 30
    }
    
    /// after user select a mode, update UI
    func tableView(_ tableView: UITableView, didSelectRowAt indexPath: IndexPath) {
        
        selectModeButton.setTitle(tableView.cellForRow(at: indexPath)?.textLabel?.text, for: .normal)
        
        UIView.animate(withDuration: 0.3) {
            self.recordingModeTableView.isHidden = true
        }
        
        selectedRecordingMode = recordingModes[indexPath.row]
        openCameraButton.isEnabled = true
        
    }
}
