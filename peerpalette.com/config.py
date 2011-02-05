from datetime import timedelta

UNREAD_THRESHOLD = 2
ALERT_THRESHOLD = 6
OFFLINE_THRESHOLD = 15
INACTIVE_THRESHOLD = 604800
STATUS_UPDATE_THRESHOLD = 8
ITEMS_PER_PAGE = 15
MAX_KEYWORDS = 4

STATUS_ONLINE = 0
STATUS_OFFLINE = 1
STATUS_INACTIVE = 2

RANDOM_CHAT_WAIT = 2

TOTAL_RESULTS = 100

AGE_INDEX_THRESHOLDS = {0 : timedelta(days = 2), 1 : timedelta(days = 9), 2 : timedelta(days = 40)}
AGE_INDEX_STEPS = len(AGE_INDEX_THRESHOLDS)

