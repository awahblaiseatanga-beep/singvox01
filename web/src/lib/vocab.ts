export const ASL_VOCAB: Record<number, string> = {
  0: "HELLO", 1: "GOOD", 2: "BAD", 3: "PLEASE", 4: "SORRY", 5: "HELP", 6: "STOP", 7: "WAIT", 8: "UNDERSTAND", 9: "YES", 10: "NO", 11: "AGAIN", 12: "SLOW", 13: "NAME", 14: "ME", 15: "YOU", 16: "FAMILY", 17: "FRIEND", 18: "MOTHER", 19: "FATHER", 20: "BROTHER", 21: "SISTER", 22: "CHILD", 23: "TEACHER", 24: "GO", 25: "COME", 26: "GIVE", 27: "TAKE", 28: "NEED", 29: "HAVE", 30: "KNOW", 31: "LIKE", 32: "SEE", 33: "THINK", 34: "LEARN", 35: "STUDY", 36: "SCHOOL", 37: "WORK", 38: "HOME", 39: "CHURCH", 40: "BATHROOM", 41: "HERE", 42: "THERE", 43: "IN", 44: "OUT", 45: "TODAY", 46: "YESTERDAY", 47: "TOMORROW", 48: "MORNING", 49: "DAY", 50: "WHO", 51: "WHERE", 52: "WHEN", 53: "WHY", 54: "WATER", 55: "HUNGRY", 56: "SLEEP", 57: "PAIN", 58: "SICK", 59: "DANGER", 60: "FIRE", 61: "COMPUTER", 62: "SIGN", 63: "LANGUAGE", 64: "HEARING", 65: "MEET", 66: "MORE", 67: "FINISH", 68: "LOVE", 69: "HAPPY", 70: "SAD", 71: "ANGRY", 72: "AFRAID", 73: "FEEL", 74: "NICE", 75: "BIG", 76: "SMALL", 77: "HOT", 78: "COLD"
};

export const PILOT_VOCAB: Record<number, string> = {
  0: "HELLO",
  1: "YES",
  2: "NO"
};

export const ASL_ALIASES: Record<string, string> = {
    "PRO1": "ME",
    "I": "ME", // Common phase "I need help" -> "ME" or unsupported. We'll add it safely.
    "PRO2": "YOU",
    "NOW": "TODAY",
    "HURT": "PAIN",
    "DONE": "FINISH",
    "OKAY": "GOOD",
    "OK": "GOOD",
    "PHONE": "CALL"
};
