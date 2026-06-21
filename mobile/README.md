# Mobile app (Phase 5 — Flutter, Android first)

Cross-platform Flutter app, built and run on **Android** first (iOS deferred; the code is
platform-neutral so an iOS build is a later `flutter build ios` away). Talks to the same FastAPI
[`backend`](../backend) over REST with a Firebase ID token, and uses Firebase for auth + push.

> ⚠️ This `lib/` tree and `pubspec.yaml` were authored without a local Flutter toolchain, so they
> have **not been compiled here**. Run `flutter analyze` after the one-time setup below and fix any
> version drift — especially in `plaid_service.dart` (the `plaid_flutter` API varies across major
> versions) and the FCM background handler.

## What's implemented

| Area | Detail |
|---|---|
| Auth | Google Sign-In ([auth_service.dart](lib/src/services/auth_service.dart)); ID token attached to every API call |
| App lock | Biometric/device-credential lock on launch + when backgrounded ([app_lock.dart](lib/src/services/app_lock.dart), [lock_screen.dart](lib/src/screens/lock_screen.dart)) |
| Dashboard | Net worth, assets, month spend/income, accounts, recent transactions |
| Transactions | List with pending/duplicate flags; tap to recategorize (creates a remembered rule) |
| Add transaction | Manual entry + **receipt capture** (camera) uploaded to Cloud Storage (OCR/matching is Phase 6) |
| Budgets | Per-category progress bars + editable monthly caps |
| Recurring | 30-day cash-flow forecast + subscriptions / recurring income |
| Alerts | Severity-iconed feed with mark-read |
| Connections | Plaid item status, **Add bank** + guided **re-auth** via Plaid Link |
| Push | FCM permission + token registered to the backend ([messaging_service.dart](lib/src/services/messaging_service.dart)) |

Architecture mirrors the web app: `services/` (auth, api_client + typed `api`, plaid, messaging,
app_lock) → `models.dart` → `screens/`, with a `RefreshBus` so a global **Sync now** reloads all tabs.

## One-time setup

```bash
cd mobile

# 1. Generate the platform folders (android/, etc.) WITHOUT touching lib/ or pubspec.yaml:
flutter create .

# 2. Resolve dependencies:
flutter pub get

# 3. Wire Firebase (writes lib/firebase_options.dart + android/app/google-services.json):
dart pub global activate flutterfire_cli
flutterfire configure
```

### Android specifics (apply after `flutter create .`)

- **minSdk** — `firebase_auth` needs `minSdkVersion 23`; set it in `android/app/build.gradle`.
- **Biometrics** — `local_auth` requires the activity to extend `FlutterFragmentActivity`. In
  `android/app/.../MainActivity.kt` change `FlutterActivity` → `FlutterFragmentActivity`, and add
  `<uses-permission android:name="android.permission.USE_BIOMETRIC"/>` to `AndroidManifest.xml`.
- **Camera** — `image_picker` needs `<uses-permission android:name="android.permission.CAMERA"/>`.
- **Plaid** — register your Android package name in the Plaid Dashboard (Allowed Android package
  names) for the OAuth redirect; `plaid_flutter` needs `minSdkVersion 21`+ (already satisfied by 23).

## Run

```bash
# Android emulator reaches the host backend at 10.0.2.2 (the default API_BASE_URL).
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000

# Physical device: point at your machine's LAN IP, e.g.
flutter run --dart-define=API_BASE_URL=http://192.168.1.20:8000
```

For a no-cloud loop, run the backend with `APP_ENV=local AUTH_DISABLED=true`; the app still needs a
real Firebase project for Google Sign-In, or stub auth out for local testing.

## Build a release APK

```bash
flutter build apk --release --dart-define=API_BASE_URL=https://<your-cloud-run-url>
```

## Not in this phase

- Receipt **OCR + transaction matching** (Phase 6 — a Cloud Storage trigger → Document AI).
- iOS build (Flutter is platform-neutral here; add via `flutter build ios` + an Apple Developer
  account / TestFlight later).
