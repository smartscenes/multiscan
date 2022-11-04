//
//  LibraryViewController.swift
//  ScannerApp-Swift
//
//  Created by Zheren Xiao on 2019-12-23.
//  Copyright © 2019 jx16. All rights reserved.
//

import UIKit

/// UI class for gallery activity
class LibraryTableViewController: UITableViewController {
    
    private let fileManager = FileManager.default
    private let cellIdentifier = "scanTableViewCell"
    
    private var fileURLs: [URL] = []
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        loadFiles()
        
//        let scanTableViewCell = UINib(nibName: "ScanTableViewCell", bundle: nil)
//        tableView.register(scanTableViewCell, forCellReuseIdentifier: cellIdentifier)
        
    }
    
    override func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return fileURLs.count
    }
    
    override func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = tableView.dequeueReusableCell(withIdentifier: cellIdentifier, for: indexPath) as! ScanTableViewCell
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

extension LibraryTableViewController: ScanTableViewCellDelegate {
    /// reload files after files are deleted successfully
    func deleteSuccess(fileId: String) {
        loadFiles()
        tableView.reloadData()
    }

    /// display a toast when files are not deleted due to errors
    func deleteFailed(fileId: String) {
        loadFiles()
        tableView.reloadData()
        Helper.showToast(controller: self, message: "Failed to delete \(fileId)", seconds: 1)
    }
    
    /// display a toast message when files did not upload to server due to errors
    func didCompletedUploadWithError(fileId: String) {
        Helper.showToast(controller: self, message: "Failed to upload \(fileId)", seconds: 1)
    }
    
    /// display a toast message when files are uploaded to server successfully
    func didCompletedUploadWithoutError(fileId: String) {
        Helper.showToast(controller: self, message: "All files in \(fileId) have been uploaded", seconds: 1)
    }
}
