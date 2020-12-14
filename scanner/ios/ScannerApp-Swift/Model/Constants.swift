//
//  Constants.swift
//  ScannerApp-Swift
//
//  Created by Zheren Xiao on 2020-02-13.
//  Copyright © 2020 jx16. All rights reserved.
//

struct Constants {
    
    static let sceneTypes: [String] = ["Please Select A Scene Type",
                                       "Apartment",
                                       "Bathroom",
                                       "Bedroom / Hotel",
                                       "Bookstore / Library",
                                       "Classroom",
                                       "Closet",
                                       "ComputerCluster",
                                       "Conference Room",
                                       "Copy Room",
                                       "Copy/Mail Room",
                                       "Dining Room",
                                       "Game room",
                                       "Gym",
                                       "Hallway",
                                       "Kitchen",
                                       "Laundromat",
                                       "Laundry Room",
                                       "Living room / Lounge",
                                       "Lobby",
                                       "Mailboxes",
                                       "Misc.",
                                       "Office",
                                       "Stairs",
                                       "Storage/Basement/Garage"]
    
    struct Server {
        
        static let chuckSize = 4096
        
        struct Endpoints {
            static let upload: String = "/upload"
            static let verify: String = "/verify"
        }

        static let defaultHost: String = "aspis.cmpt.sfu.ca:80/multiscan"
    }

}
