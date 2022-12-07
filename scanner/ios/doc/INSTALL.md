## Install scanner app to iPad

1. Open project file `ScannerApp-Swift.xcodeproj file` on Mac
2. In the left project navigator window, click the first project file, and select `TARGETS ScannerApp-Swift`. 
3. In `Build Settings`, find the field `Signing/Development Team`, change the team to your personal team. If you don't see your personal team option, please sign in your apple account in the `Xcode/Preferences/Accounts`.
4. In `Build Settings`, find the field `Packaging/Product Bundle Identifier`, change the identifier to `username.ScannerApp`.
5. On the top bar, switch device to iOS Device to your iPad.
6. Build and run the current scheme, and the scanner app should be installed to your iPad device.