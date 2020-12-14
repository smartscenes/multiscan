//
//  PopUpView.swift
//  ScannerApp-Swift
//
//  Created by Zheren Xiao on 2020-10-21.
//  Copyright © 2020 jx16. All rights reserved.
//

import UIKit

class PopUpView: UIView {
    
    let sceneTypes = Constants.sceneTypes

    var firstName: String = ""
    var lastName: String = ""
    var userInputDescription: String = ""
    var sceneTypeIndex = 0
//    private var sceneType: String?
    
    private var textFieldIsBeingEdited: Bool = false
    
    init() {
        
        super.init(frame: .zero)
        
        // load UserDefaults
        firstName = UserDefaults.firstName
        lastName = UserDefaults.lastName
        userInputDescription = UserDefaults.userInputDescription
        sceneTypeIndex = UserDefaults.sceneTypeIndex
        
        firstNameTextField.text = firstName
        lastNameTextField.text = lastName
        descriptionTextField.text = userInputDescription
        sceneTypePickerView.selectRow(sceneTypeIndex, inComponent: 0, animated: false)

        setupViews()
        updateStartButton()
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    let firstNameLabel: UILabel = {
        let lb = UILabel()
        lb.text = "First Name"
        return lb
    }()
    
    let lastNameLabel: UILabel = {
        let lb = UILabel()
        lb.text = "Last Name"
        return lb
    }()
    
    let descriptionLabel: UILabel = {
        let lb = UILabel()
        lb.text = "Description"
        return lb
    }()
    
    lazy var firstNameTextField: UITextField = {
        let tf = UITextField()
        tf.placeholder = "Enter first name"
        tf.layer.borderColor = UIColor.lightGray.cgColor
        tf.layer.borderWidth = 1
        tf.delegate = self
        tf.autocorrectionType = .no
        return tf
    }()
    
    lazy var lastNameTextField: UITextField = {
        let tf = UITextField()
        tf.placeholder = "Enter last name"
        tf.layer.borderColor = UIColor.lightGray.cgColor
        tf.layer.borderWidth = 1
        tf.delegate = self
        tf.autocorrectionType = .no
        return tf
    }()
    
    lazy var descriptionTextField: UITextField = {
        let tf = UITextField()
        tf.placeholder = "Enter scene description"
        tf.layer.borderColor = UIColor.lightGray.cgColor
        tf.layer.borderWidth = 1
        tf.delegate = self
        tf.autocorrectionType = .no
        return tf
    }()
    
    lazy var sceneTypePickerView: UIPickerView = {
        let pv = UIPickerView()
        pv.delegate = self
        pv.dataSource = self
        pv.selectRow(sceneTypeIndex, inComponent: 0, animated: false)
        return pv
    }()
    
    weak var delegate: CameraViewControllerPopUpViewDelegate?
    
    let cancelButton: UIButton = {
        let btn = UIButton(type: .system)
        btn.setTitle("Cancel", for: .normal)
        btn.addTarget(self, action: #selector(cancelButtonTapped), for: .touchUpInside)
        return btn
    }()
    
    @objc func cancelButtonTapped() {
        print("Cancel button tapped")
        delegate?.dismissPopUpView()
    }
    
    let startButton: UIButton = {
        let btn = UIButton(type: .system)
        btn.setTitle("Start Recording", for: .normal)
        btn.isEnabled = false
        btn.addTarget(self, action: #selector(startButtonTapped), for: .touchUpInside)
        return btn
    }()
    
    @objc func startButtonTapped() {
        print("Start button tapped")
        delegate?.startRecording()
    }
    
    func setupViews() {
        
        self.translatesAutoresizingMaskIntoConstraints = false
        self.heightAnchor.constraint(equalToConstant: 420).isActive = true
        self.widthAnchor.constraint(equalToConstant: 330).isActive = true
        self.backgroundColor = UIColor(white: 1, alpha: 0.8)
        
        // first name row
        addSubview(firstNameLabel)
        firstNameLabel.translatesAutoresizingMaskIntoConstraints = false
        firstNameLabel.heightAnchor.constraint(equalToConstant: 50).isActive = true
        firstNameLabel.widthAnchor.constraint(equalToConstant: 90).isActive = true
        firstNameLabel.topAnchor.constraint(equalTo: topAnchor, constant: 8).isActive = true
        firstNameLabel.leftAnchor.constraint(equalTo: leftAnchor, constant: 8).isActive = true
        
        addSubview(firstNameTextField)
        firstNameTextField.translatesAutoresizingMaskIntoConstraints = false
        firstNameTextField.heightAnchor.constraint(equalTo: firstNameLabel.heightAnchor).isActive = true
        firstNameTextField.topAnchor.constraint(equalTo: firstNameLabel.topAnchor).isActive = true
        firstNameTextField.leftAnchor.constraint(equalTo: firstNameLabel.rightAnchor, constant: 8).isActive = true
        firstNameTextField.rightAnchor.constraint(equalTo: rightAnchor, constant: -8).isActive = true

        // last name row
        addSubview(lastNameLabel)
        lastNameLabel.translatesAutoresizingMaskIntoConstraints = false
        lastNameLabel.heightAnchor.constraint(equalToConstant: 50).isActive = true
        lastNameLabel.widthAnchor.constraint(equalToConstant: 90).isActive = true
        lastNameLabel.topAnchor.constraint(equalTo: firstNameLabel.bottomAnchor, constant: 8).isActive = true
        lastNameLabel.leftAnchor.constraint(equalTo: leftAnchor, constant: 8).isActive = true
        
        addSubview(lastNameTextField)
        lastNameTextField.translatesAutoresizingMaskIntoConstraints = false
        lastNameTextField.heightAnchor.constraint(equalTo: lastNameLabel.heightAnchor).isActive = true
        lastNameTextField.topAnchor.constraint(equalTo: lastNameLabel.topAnchor).isActive = true
        lastNameTextField.leftAnchor.constraint(equalTo: lastNameLabel.rightAnchor, constant: 8).isActive = true
        lastNameTextField.rightAnchor.constraint(equalTo: rightAnchor, constant: -8).isActive = true
        
        // description row
        addSubview(descriptionLabel)
        descriptionLabel.translatesAutoresizingMaskIntoConstraints = false
        descriptionLabel.heightAnchor.constraint(equalToConstant: 50).isActive = true
        descriptionLabel.widthAnchor.constraint(equalToConstant: 90).isActive = true
        descriptionLabel.topAnchor.constraint(equalTo: lastNameLabel.bottomAnchor, constant: 8).isActive = true
        descriptionLabel.leftAnchor.constraint(equalTo: leftAnchor, constant: 8).isActive = true

        addSubview(descriptionTextField)
        descriptionTextField.translatesAutoresizingMaskIntoConstraints = false
        descriptionTextField.heightAnchor.constraint(equalTo: descriptionLabel.heightAnchor).isActive = true
        descriptionTextField.topAnchor.constraint(equalTo: descriptionLabel.topAnchor).isActive = true
        descriptionTextField.leftAnchor.constraint(equalTo: descriptionLabel.rightAnchor, constant: 8).isActive = true
        descriptionTextField.rightAnchor.constraint(equalTo: rightAnchor, constant: -8).isActive = true
        
        addSubview(sceneTypePickerView)
        sceneTypePickerView.translatesAutoresizingMaskIntoConstraints = false
        sceneTypePickerView.heightAnchor.constraint(equalToConstant: 180).isActive = true
        sceneTypePickerView.topAnchor.constraint(equalTo: descriptionLabel.bottomAnchor, constant: 8).isActive = true
        sceneTypePickerView.leftAnchor.constraint(equalTo: leftAnchor, constant: 8).isActive = true
        sceneTypePickerView.rightAnchor.constraint(equalTo: rightAnchor, constant: -8).isActive = true
        
        addSubview(cancelButton)
        cancelButton.translatesAutoresizingMaskIntoConstraints = false
        cancelButton.heightAnchor.constraint(equalToConstant: 40).isActive = true
        cancelButton.topAnchor.constraint(equalTo: sceneTypePickerView.bottomAnchor, constant: 8).isActive = true
        cancelButton.leftAnchor.constraint(equalTo: leftAnchor, constant: 20).isActive = true
        cancelButton.rightAnchor.constraint(equalTo: centerXAnchor, constant: -20).isActive = true
//        cancelButton.backgroundColor = .yellow
        
        addSubview(startButton)
        startButton.translatesAutoresizingMaskIntoConstraints = false
        startButton.heightAnchor.constraint(equalToConstant: 40).isActive = true
        startButton.topAnchor.constraint(equalTo: sceneTypePickerView.bottomAnchor, constant: 8).isActive = true
        startButton.leftAnchor.constraint(equalTo: centerXAnchor, constant: 20).isActive = true
        startButton.rightAnchor.constraint(equalTo: rightAnchor, constant: -20).isActive = true
//        startButton.backgroundColor = .yellow
        
    }
    
    private func updateStartButton() {
        DispatchQueue.main.async {
            if !self.textFieldIsBeingEdited && self.hasAllRequiredUserInput() {
                self.startButton.isEnabled = true
            } else {
                self.startButton.isEnabled = false
            }
        }
    }
    
    private func hasAllRequiredUserInput() -> Bool {
        if !firstName.isEmpty
            && !lastName.isEmpty
            && !userInputDescription.isEmpty
            && sceneTypeIndex != 0 {
            return true
        } else {
            return false
        }
    }
    
}

extension PopUpView: UITextFieldDelegate {
    
    func textFieldDidBeginEditing(_ textField: UITextField) {
        textFieldIsBeingEdited = true

        // disable start button when editing text field
        updateStartButton()
    }
    
    func textFieldDidEndEditing(_ textField: UITextField) {
        textFieldIsBeingEdited = false
        
        let text: String = (textField.text ?? "").trimmingCharacters(in: .whitespaces)
        
        switch textField {
        case firstNameTextField:
            print("setting first name to '\(text)'.")
            firstName = text
            UserDefaults.set(firstName: text)
        case lastNameTextField:
            print("setting last name to '\(text)'.")
            lastName = text
            UserDefaults.set(lastName: text)
        case descriptionTextField:
            print("setting description to '\(text)'.")
            userInputDescription = text
            UserDefaults.set(userInputDescription: text)
        default:
            print("text field '\(textField.description)' is not found.")
        }
        
        updateStartButton()
    }
    
    func textFieldShouldReturn(_ textField: UITextField) -> Bool {
        print("dismiss keyboard")
        textField.resignFirstResponder()
        return true
    }
}

extension PopUpView: UIPickerViewDelegate, UIPickerViewDataSource {
    func numberOfComponents(in pickerView: UIPickerView) -> Int {
        return 1;
    }
    
    func pickerView(_ pickerView: UIPickerView, numberOfRowsInComponent component: Int) -> Int {
        return sceneTypes.count
    }
    
    func pickerView(_ pickerView: UIPickerView, titleForRow row: Int, forComponent component: Int) -> String? {
        return sceneTypes[row]
    }
    
    func pickerView(_ pickerView: UIPickerView, didSelectRow row: Int, inComponent component: Int) {
        sceneTypeIndex = row
        UserDefaults.set(sceneTypeIndex: row)

        updateStartButton()
    }
}

