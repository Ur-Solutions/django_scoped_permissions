import os

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY = "scoped-permissions-test-only-secret"
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
DEBUG = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "django_scoped_permissions",
    "django_scoped_permissions.tests",
    "graphene_django",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "django_test.sqlite"}
}

# Only disposable test databases belong here. pytest-django creates and drops
# test_scoped_permissions; it never needs access to an application's database.
TEST_DATABASE = os.environ.get("SCOPED_TEST_DATABASE", "sqlite")
if TEST_DATABASE in {"postgresql", "mssql"}:
    DATABASES["default"] = {
        "ENGINE": "mssql" if TEST_DATABASE == "mssql" else "django.db.backends.postgresql",
        "NAME": "master" if TEST_DATABASE == "mssql" else "postgres",
        "HOST": os.environ.get("SCOPED_TEST_HOST", "127.0.0.1"),
        "PORT": os.environ.get("SCOPED_TEST_PORT", "1433" if TEST_DATABASE == "mssql" else "5432"),
        "USER": os.environ.get("SCOPED_TEST_USER", "sa" if TEST_DATABASE == "mssql" else "postgres"),
        "PASSWORD": os.environ["SCOPED_TEST_PASSWORD"],
        "TEST": {"NAME": "test_scoped_permissions"},
    }
    if TEST_DATABASE == "mssql":
        DATABASES["default"]["OPTIONS"] = {
            "driver": "ODBC Driver 18 for SQL Server",
            "extra_params": "TrustServerCertificate=yes",
            "connection_retries": 12,
            "connection_retry_backoff_time": 5,
        }
elif TEST_DATABASE != "sqlite":
    raise ValueError(f"Unknown SCOPED_TEST_DATABASE: {TEST_DATABASE}")

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

GRAPHENE = {"SCHEMA": "django_scoped_permissions.tests.schema.schema"}

AUTH_USER_MODEL = "tests.User"

STATIC_URL = "/static/"
STATIC_ROOT = "static/"
ROOT_URLCONF = "django_scoped_permissions.tests.urls"
