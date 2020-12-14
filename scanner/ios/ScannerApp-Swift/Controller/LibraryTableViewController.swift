//
//  LibraryViewController.swift
//  ScannerApp-Swift
//
//  Created by Zheren Xiao on 2019-12-23.
//  Copyright © 2019 jx16. All rights reserved.
//

import UIKit

class LibraryTableViewController: UITableViewController {
    
    private let fileManager = FileManager.default
    private let cellIdentifier = "libraryTableViewCell"
    
    private var fileURLs: [URL] = []
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        loadFiles()
        
//        let scanTableViewCell = UINib(nibName: "ScanTableViewCell", bundle: nil)
//        tableView.register(scanTableViewCell, forCellReuseIdentifier: cellIdentifier)
        
    }
    
//    override func tableView(_ tableView: UITableView, didSelectRowAt indexPath: IndexPath) {
//        let selectedRecordingUrl = fileURLs[indexPath.row]
//
//        // iOS 13.0+
////        if let viewController = storyboard?.instantiateViewController(identifier: "RecordingDetailViewController") as? RecordingDetailViewController {
////            viewController.recordingUrl = selectedRecordingUrl
////            navigationController?.pushViewController(viewController, animated: true)
////        }
//
//        if let viewController = storyboard?.instantiateViewController(withIdentifier: "RecordingDetailViewController") as? RecordingDetailViewController {
//            viewController.recordingUrl = selectedRecordingUrl
//            navigationController?.pushViewController(viewController, animated: true)
//        }
//    }
    
    override func prepare(for segue: UIStoryboardSegue, sender: Any?) {
        if segue.identifier == "ShowRecordingDetail" {
            let selectedRecordingUrl = fileURLs[tableView.indexPathForSelectedRow!.row]
            if let viewController = segue.destination as? RecordingDetailViewController {
                viewController.recordingUrl = selectedRecordingUrl
            }
        }
    }
    
    override func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return fileURLs.count
    }
    
    override func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = tableView.dequeueReusableCell(withIdentifier: cellIdentifier, for: indexPath) as! LibraryTableViewCell
//        cell.textLabel?.text = fileURLs[indexPath.item].lastPathComponent
//        cell.textLabel?.text = fileURLs[indexPath.item].absoluteString
        
        cell.setupCellWithURL(url: fileURLs[indexPath.item])
        cell.scanTableViewCellDelegate = self
        return cell
    }
    
    override func tableView(_ tableView: UITableView, heightForRowAt indexPath: IndexPath) -> CGFloat {
        return 150
    }
    
    private func loadFiles() {
        let documentsURL = fileManager.urls(for: .documentDirectory, in: .userDomainMask)[0]
        do {
            fileURLs = try fileManager.contentsOfDirectory(at: documentsURL, includingPropertiesForKeys: nil)
            
        } catch {
            print("Error while enumerating files \(documentsURL.path): \(error.localizedDescription)")
        }
    }
}

extension LibraryTableViewController: LibraryTableViewCellDelegate {
    
    func deleteSuccess(recordingId: String) {
        loadFiles()
        tableView.reloadData()
    }
    
    func deleteFailed(recordingId: String) {
        loadFiles()
        tableView.reloadData()
        Helper.showToast(controller: self, message: "Failed to delete \(recordingId)", seconds: 1)
    }
    
    func didCompletedUploadWithError(recordingId: String) {
        Helper.showToast(controller: self, message: "Failed to upload \(recordingId)", seconds: 1)
    }
    
    func didCompletedUploadWithoutError(recordingId: String) {
        Helper.showToast(controller: self, message: "All files in \(recordingId) have been uploaded", seconds: 1)
    }
}
