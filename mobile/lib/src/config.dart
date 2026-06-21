/// App configuration. The API base URL is provided at build time via
/// `--dart-define=API_BASE_URL=...`. The default targets the FastAPI backend from the Android
/// emulator (10.0.2.2 is the emulator's alias for the host machine's localhost).
class Config {
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );
}
