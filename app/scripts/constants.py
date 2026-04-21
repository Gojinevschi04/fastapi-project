"""Constants shared across seed scripts."""

# Demo user accounts
ADMIN_EMAIL_PRIMARY = "ana.gojinevschi@isa.utm.md"
ADMIN_EMAIL_SECONDARY = "annagojinevschi@gmail.com"
ADMIN_PASSWORD = "admin1234"
USER_PASSWORD = "password123"

# Demo data generation
SECONDS_BETWEEN_TRANSCRIPT_LINES = 8
DEMO_RECORDING_URL_TEMPLATE = "https://api.twilio.com/2010-04-01/Accounts/DEMO/Recordings/RE{task_id:06d}.wav"
MIN_TASK_COUNT_TO_SKIP = 10
BASE_CALL_DURATION_SECONDS = 45
CALL_DURATION_VARIATION_FACTOR = 7
MAX_CALL_DURATION_VARIATION = 120
