//
//  ScanListTableViewCell.swift
//  ScannerApp-Swift
//
//  Created by Zheren Xiao on 2019-12-23.
//  Copyright © 2019 jx16. All rights reserved.
//

import AVFoundation
import UIKit

protocol LibraryTableViewCellDelegate {
    func deleteSuccess(recordingId: String)
    func deleteFailed(recordingId: String)
    func didCompletedUploadWithError(recordingId: String)
    func didCompletedUploadWithoutError(recordingId: String)
}

class LibraryTableViewCell: UITableViewCell {

    private var url: URL!
    var scanTableViewCellDelegate: LibraryTableViewCellDelegate!
    
    @IBOutlet weak var thumbnail: UIImageView!
    @IBOutlet weak var titleLabel: UILabel!
    @IBOutlet weak var infoLabel: UILabel!
    @IBOutlet weak var uploadButton: UIButton!
    @IBOutlet weak var deleteButton: UIButton!
    @IBOutlet weak var uploadProgressView: UIProgressView!
    
    override func awakeFromNib() {
        super.awakeFromNib()
        // Initialization code
    }

    override func setSelected(_ selected: Bool, animated: Bool) {
        super.setSelected(selected, animated: animated)

        // Configure the view for the selected state
    }
    
    func setupCellWithURL(url: URL) {
        self.url = url
        
        self.titleLabel.text = url.lastPathComponent
        
        if url.hasDirectoryPath {
            var fileURLs: [URL] = []
            do {
                fileURLs = try FileManager.default.contentsOfDirectory(at: url, includingPropertiesForKeys: nil)
            } catch {
                print("Error while enumerating files \(url.path): \(error.localizedDescription)")
            }
            
            var infoText = ""
            for fileUrl in fileURLs {
                let extention = fileUrl.pathExtension
                infoText = infoText + extention + " "
                
                if extention == "mp4" {
                    let cgImage = VideoHelper.generateThumbnail(videoUrl: fileUrl)
                    if cgImage != nil {
                        self.thumbnail.image = UIImage(cgImage: cgImage!)
                    }
                }
            }
            
            self.infoLabel.text = infoText
            
        } else {
            self.infoLabel.text = url.pathExtension
        }
        
        self.infoLabel.textColor = .darkGray
        
        self.uploadProgressView.isHidden = true
    }
    
    // TODO: behavior related stuff probably should be in a controller class
    @IBAction func uploadButtonTapped(_ sender: Any) {
        DispatchQueue.main.async {
            self.uploadButton.isEnabled = false
            self.deleteButton.isEnabled = false
            self.uploadProgressView.isHidden = false
        }
        
        let requestHandler = HttpRequestHandler(delegate: self)
        requestHandler.upload(toUpload: url)
    }
    
    @IBAction func deleteButtonTapped(_ sender: Any) {
        do {
            try FileManager.default.removeItem(at: url)
            scanTableViewCellDelegate.deleteSuccess(recordingId: url.lastPathComponent)
        } catch {
            print("failed to remove \(url.absoluteString)")
            scanTableViewCellDelegate.deleteFailed(recordingId: url.lastPathComponent)
        }
    }
}

extension LibraryTableViewCell: HttpRequestHandlerDelegate {
    
    func didReceiveUploadProgressUpdate(progress: Float) {
//        print(progress)
        DispatchQueue.main.async {
            self.uploadProgressView.progress = progress
        }
    }
    
    func didCompletedUploadWithError() {

        DispatchQueue.main.async {
            self.uploadButton.isEnabled = true
            self.deleteButton.isEnabled = true
            self.uploadProgressView.isHidden = true
            
            self.scanTableViewCellDelegate.didCompletedUploadWithError(recordingId: self.url.lastPathComponent)
        }
    }
    
    func didCompletedUploadWithoutError() {
        DispatchQueue.main.async {
            self.uploadButton.isEnabled = true
            self.deleteButton.isEnabled = true
            self.uploadProgressView.isHidden = true
            
            self.scanTableViewCellDelegate.didCompletedUploadWithoutError(recordingId: self.url.lastPathComponent)
        }
    }
}
