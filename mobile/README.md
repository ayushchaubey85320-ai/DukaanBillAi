# 📱 DukaanAI Mobile Application (Android & iOS)

This folder contains the React Native code and Capacitor configuration for packaging DukaanAI into native Android (APK) and iOS applications.

## Option A: React Native / Expo
1. Install dependencies:
   ```bash
   npx create-expo-app DukaanAIMobile --template blank-typescript
   cd DukaanAIMobile
   ```
2. Copy `mobile/App.tsx` into your Expo project's `App.tsx`.
3. Start the app:
   ```bash
   npx expo start
   ```
4. Scan the QR code using Expo Go on your Android device or iPhone!

## Option B: Progressive Web App / Capacitor (Recommended)
You can directly package the `frontend` web application into native APK & iOS projects using Capacitor:
```bash
cd frontend
npm install @capacitor/core @capacitor/cli @capacitor/android @capacitor/ios
npx cap init DukaanAI com.dukaanai.app --web-dir dist
npm run build
npx cap add android
npx cap add ios
npx cap open android
```
This generates standard Android Studio and Xcode projects with native hardware mic and printer support.
