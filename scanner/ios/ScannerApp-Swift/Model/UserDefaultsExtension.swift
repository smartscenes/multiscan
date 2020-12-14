//
//  ScannerAppUserDefualts.swift
//  ScannerApp-Swift
//
//  Created by Zheren Xiao on 2020-04-22.
//  Copyright © 2020 jx16. All rights reserved.
//

import Foundation

extension UserDefaults {
    
    struct Keys {
        static let firstName = "firstNameKey"
        static let lastName = "lastNameKey"
        static let sceneTypeIndex = "sceneTypeIndexKey"
        static let userInputDescription = "userInputDescriptionKey"
        static let debugFlag = "debugFlagKey"
        static let host = "hostKey"
    }
    
    /// firstName
    class var firstName: String {
        let userDefaults = UserDefaults.standard
        if let firstName = userDefaults.string(forKey: UserDefaults.Keys.firstName) {
            return firstName
        } else {
//            UserDefaults.set(firstName: "")
            return ""
        }
    }
    
    class func set(firstName: String) {
        let userDefaults = UserDefaults.standard
        userDefaults.set(firstName, forKey: UserDefaults.Keys.firstName)
    }
    
    /// lastName
    class var lastName: String {
        let userDefaults = UserDefaults.standard
        if let lastName = userDefaults.string(forKey: UserDefaults.Keys.lastName) {
            return lastName
        } else {
            return ""
        }
    }
    
    class func set(lastName: String) {
        let userDefaults = UserDefaults.standard
        userDefaults.set(lastName, forKey: UserDefaults.Keys.lastName)
    }

    /// sceneTypeIndex
    class var sceneTypeIndex: Int {
        let userDefaults = UserDefaults.standard
        
        // UserDefault.integer return non-optional value, nil check not needed
        // the following return statement return 0 if the specified key doesn‘t exist
        return userDefaults.integer(forKey: UserDefaults.Keys.sceneTypeIndex)
    }
    
    class func set(sceneTypeIndex: Int) {
        let userDefaults = UserDefaults.standard
        userDefaults.set(sceneTypeIndex, forKey: UserDefaults.Keys.sceneTypeIndex)
    }
    
    /// userInputDescription
    class var userInputDescription: String {
        let userDefaults = UserDefaults.standard
        if let userInputDescription = userDefaults.string(forKey: UserDefaults.Keys.userInputDescription) {
            return userInputDescription
        } else {
            return ""
        }
    }
    
    class func set(userInputDescription: String) {
        let userDefaults = UserDefaults.standard
        userDefaults.set(userInputDescription, forKey: UserDefaults.Keys.userInputDescription)
    }
    
    /// debugFlag
    class var debugFlag: Bool {
        let userDefaults = UserDefaults.standard
        return userDefaults.bool(forKey: UserDefaults.Keys.debugFlag)
    }
    
    class func set(debugFlag: Bool) {
        let userDefaults = UserDefaults.standard
        userDefaults.set(debugFlag, forKey: UserDefaults.Keys.debugFlag)
    }
    
    /// host
    class var host: String {
        let userDefaults = UserDefaults.standard
        return userDefaults.string(forKey: UserDefaults.Keys.host) ?? ""
    }
    
    class func set(host: String) {
        let userDefaults = UserDefaults.standard
        userDefaults.set(host, forKey: UserDefaults.Keys.host)
    }

}
