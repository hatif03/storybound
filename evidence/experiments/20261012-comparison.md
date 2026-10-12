| Run | Stories | Outcomes | Errors | First pass broke | Shipped a break | Repairs / story | Seconds (mean, max) | Est. USD / story | Quiz shown | Degradations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| holdout-routes-default | 10 | {'shipped': 9, 'shipped_with_notes': 1} | 0 | 8 | 1 | 2.4 | 158, 254 | 0.0242 | 35 | {} |
| C1-stall-hedge-on | 5 | {'shipped': 5} | 0 | 4 | 0 | 2.4 | 244, 471 | 0.023 | 17 | {} |
| C2-stall-hedge-off | 5 | {'shipped': 5} | 0 | 5 | 0 | 2.4 | 294, 415 | 0.0225 | 16 | {} |
| C3-gemini-503 | 5 | {'refused': 1, 'shipped': 4} | 0 | 3 | 0 | 1.2 | 169, 299 | 0.0169 | 14 | {} |
| C3b-gemini-503-after-fix | 5 | {'error': 1, 'shipped': 4} | 1 | 3 | 0 | 1.75 | 213, 277 | 0.0209 | 13 | {} |
| C4-judge-down | 5 | {'stopped': 3, 'refused': 1, 'error': 1} | 1 | 0 | 0 | 0.0 | 0, 0 | 0.0 | 0 | {} |
| C4b-judge-down-failover | 5 | {'shipped': 5} | 0 | 3 | 0 | 2.2 | 167, 248 | 0.1292 | 18 | {} |
| C5-gateway-down | 5 | {'shipped': 5} | 0 | 2 | 0 | 0.4 | 197, 266 | 0.0158 | 19 | {} |
| C6-image-429 | 3 | {'shipped': 2, 'shipped_with_notes': 1} | 0 | 3 | 1 | 2.0 | 1386, 1561 | 0.2664 | 12 | {'image': 12} |
| C7-both-judges-down | 5 | {'error': 5} | 5 | 0 | 0 | 0.0 | 0, 0 | 0.0 | 0 | {} |
| X1-writer-gemini-pro | 10 | {'shipped': 10} | 0 | 9 | 0 | 1.3 | 213, 334 | 0.1129 | 34 | {} |
| X2-writer-claude-sonnet | 10 | {'shipped': 6, 'error': 3, 'shipped_with_notes': 1} | 3 | 5 | 1 | 2.71 | 138, 393 | 0.0913 | 26 | {} |
| X2b-writer-claude-sonnet-fixed | 10 | {'shipped': 10} | 0 | 10 | 0 | 5.1 | 218, 318 | 0.1224 | 34 | {} |
| X3-judge-ensemble | 10 | {'shipped': 10} | 0 | 9 | 0 | 3.6 | 241, 440 | 0.1375 | 32 | {} |
| X4-no-judge | 10 | {'shipped': 9, 'shipped_with_notes': 1} | 0 | 5 | 1 | 1.1 | 49, 62 | 0.0199 | 34 | {} |
| X5-repairs-0 | 10 | {'shipped': 4, 'shipped_with_notes': 6} | 0 | 7 | 6 | 0.4 | 154, 274 | 0.0184 | 37 | {} |
| X6-repairs-4 | 10 | {'shipped': 10} | 0 | 9 | 0 | 2.5 | 177, 377 | 0.0224 | 34 | {} |

```json
{
 "holdout-routes-default": {
  "n": 10,
  "outcomes": {
   "shipped": 9,
   "shipped_with_notes": 1
  },
  "errors": 0,
  "first_pass_broke": 8,
  "shipped_break": 1,
  "repairs": 2.4,
  "seconds": 158,
  "p_max_seconds": 254,
  "usd_est": 0.0242,
  "quiz_shown": 35,
  "degradations": {},
  "models": {
   "gemini-3.7-flash": [
    116659,
    33103,
    176
   ],
   "IFM/K2-Horizon-375B-A23B": [
    135768,
    149081,
    183
   ],
   "nova-2-lite": [
    3484,
    8611,
    10
   ],
   "claude-haiku": [
    16279,
    7523,
    15
   ]
  }
 },
 "C1-stall-hedge-on": {
  "n": 5,
  "outcomes": {
   "shipped": 5
  },
  "errors": 0,
  "first_pass_broke": 4,
  "shipped_break": 0,
  "repairs": 2.4,
  "seconds": 244,
  "p_max_seconds": 471,
  "usd_est": 0.023,
  "quiz_shown": 17,
  "degradations": {},
  "models": {
   "gemini-3.7-flash": [
    54158,
    15084,
    83
   ],
   "IFM/K2-Horizon-375B-A23B": [
    67495,
    74379,
    92
   ],
   "nova-2-lite": [
    1708,
    4212,
    5
   ],
   "claude-haiku": [
    8640,
    3834,
    8
   ]
  }
 },
 "C2-stall-hedge-off": {
  "n": 5,
  "outcomes": {
   "shipped": 5
  },
  "errors": 0,
  "first_pass_broke": 5,
  "shipped_break": 0,
  "repairs": 2.4,
  "seconds": 294,
  "p_max_seconds": 415,
  "usd_est": 0.0225,
  "quiz_shown": 16,
  "degradations": {},
  "models": {
   "gemini-3.7-flash": [
    49582,
    14120,
    76
   ],
   "IFM/K2-Horizon-375B-A23B": [
    61112,
    65844,
    81
   ],
   "nova-2-lite": [
    1708,
    3673,
    5
   ],
   "claude-haiku": [
    9863,
    4289,
    9
   ]
  }
 },
 "C3-gemini-503": {
  "n": 5,
  "outcomes": {
   "refused": 1,
   "shipped": 4
  },
  "errors": 0,
  "first_pass_broke": 3,
  "shipped_break": 0,
  "repairs": 1.2,
  "seconds": 169,
  "p_max_seconds": 299,
  "usd_est": 0.0169,
  "quiz_shown": 14,
  "degradations": {},
  "models": {
   "gemini-3.7-flash": [
    38572,
    11061,
    59
   ],
   "IFM/K2-Horizon-375B-A23B": [
    49084,
    47313,
    65
   ],
   "nova-2-lite": [
    1358,
    3030,
    4
   ],
   "claude-haiku": [
    6557,
    2898,
    6
   ]
  }
 },
 "C3b-gemini-503-after-fix": {
  "n": 5,
  "outcomes": {
   "error": 1,
   "shipped": 4
  },
  "errors": 1,
  "first_pass_broke": 3,
  "shipped_break": 0,
  "repairs": 1.75,
  "seconds": 213,
  "p_max_seconds": 277,
  "usd_est": 0.0209,
  "quiz_shown": 13,
  "degradations": {},
  "models": {
   "gemini-3.7-flash": [
    36451,
    9714,
    54
   ],
   "IFM/K2-Horizon-375B-A23B": [
    47645,
    38666,
    62
   ],
   "nova-2-lite": [
    1385,
    3332,
    4
   ],
   "claude-haiku": [
    7658,
    3303,
    7
   ]
  }
 },
 "C4-judge-down": {
  "n": 5,
  "outcomes": {
   "stopped": 3,
   "refused": 1,
   "error": 1
  },
  "errors": 1,
  "first_pass_broke": 0,
  "shipped_break": 0,
  "repairs": 0.0,
  "seconds": 0,
  "p_max_seconds": 0,
  "usd_est": 0.0,
  "quiz_shown": 0,
  "degradations": {},
  "models": {}
 },
 "C4b-judge-down-failover": {
  "n": 5,
  "outcomes": {
   "shipped": 5
  },
  "errors": 0,
  "first_pass_broke": 3,
  "shipped_break": 0,
  "repairs": 2.2,
  "seconds": 167,
  "p_max_seconds": 248,
  "usd_est": 0.1292,
  "quiz_shown": 18,
  "degradations": {},
  "models": {
   "gemini-3.7-flash": [
    60534,
    17255,
    95
   ],
   "claude-sonnet-4.6": [
    76754,
    16394,
    95
   ],
   "nova-2-lite": [
    1690,
    4061,
    5
   ],
   "claude-haiku": [
    7601,
    3618,
    7
   ]
  }
 },
 "C5-gateway-down": {
  "n": 5,
  "outcomes": {
   "shipped": 5
  },
  "errors": 0,
  "first_pass_broke": 2,
  "shipped_break": 0,
  "repairs": 0.4,
  "seconds": 197,
  "p_max_seconds": 266,
  "usd_est": 0.0158,
  "quiz_shown": 19,
  "degradations": {},
  "models": {
   "gemini-3.7-flash": [
    48522,
    18218,
    71
   ],
   "IFM/K2-Horizon-375B-A23B": [
    57380,
    65852,
    74
   ]
  }
 },
 "C6-image-429": {
  "n": 3,
  "outcomes": {
   "shipped": 2,
   "shipped_with_notes": 1
  },
  "errors": 0,
  "first_pass_broke": 3,
  "shipped_break": 1,
  "repairs": 2.0,
  "seconds": 1386,
  "p_max_seconds": 1561,
  "usd_est": 0.2664,
  "quiz_shown": 12,
  "degradations": {
   "image": 12
  },
  "models": {
   "gemini-3.7-flash": [
    48768,
    11235,
    65
   ],
   "IFM/K2-Horizon-375B-A23B": [
    44658,
    48568,
    61
   ],
   "nova-2-lite": [
    1023,
    2130,
    3
   ],
   "claude-haiku": [
    28594,
    2809,
    19
   ],
   "gemini-2.5-flash-image": [
    14238,
    10320,
    8
   ],
   "gemini-2.5-flash-tts": [
    0,
    0,
    24
   ],
   "gemini-3.1-flash-image": [
    9275,
    8960,
    8
   ]
  }
 },
 "C7-both-judges-down": {
  "n": 5,
  "outcomes": {
   "error": 5
  },
  "errors": 5,
  "first_pass_broke": 0,
  "shipped_break": 0,
  "repairs": 0.0,
  "seconds": 0,
  "p_max_seconds": 0,
  "usd_est": 0.0,
  "quiz_shown": 0,
  "degradations": {},
  "models": {}
 },
 "X1-writer-gemini-pro": {
  "n": 10,
  "outcomes": {
   "shipped": 10
  },
  "errors": 0,
  "first_pass_broke": 9,
  "shipped_break": 0,
  "repairs": 1.3,
  "seconds": 213,
  "p_max_seconds": 334,
  "usd_est": 0.1129,
  "quiz_shown": 34,
  "degradations": {},
  "models": {
   "gemini-3.7-flash": [
    31135,
    10079,
    30
   ],
   "IFM/K2-Horizon-375B-A23B": [
    119097,
    150278,
    161
   ],
   "nova-2-lite": [
    3441,
    8160,
    10
   ],
   "gemini-3.1-pro-preview": [
    55036,
    93272,
    99
   ],
   "claude-haiku": [
    16164,
    7361,
    16
   ]
  }
 },
 "X2-writer-claude-sonnet": {
  "n": 10,
  "outcomes": {
   "shipped": 6,
   "error": 3,
   "shipped_with_notes": 1
  },
  "errors": 3,
  "first_pass_broke": 5,
  "shipped_break": 1,
  "repairs": 2.71,
  "seconds": 138,
  "p_max_seconds": 393,
  "usd_est": 0.0913,
  "quiz_shown": 26,
  "degradations": {},
  "models": {
   "gemini-3.7-flash": [
    21784,
    7009,
    21
   ],
   "IFM/K2-Horizon-375B-A23B": [
    101557,
    110689,
    129
   ],
   "nova-2-lite": [
    2420,
    5616,
    7
   ],
   "claude-sonnet-4.6": [
    57945,
    21815,
    90
   ],
   "claude-haiku": [
    10769,
    5087,
    9
   ]
  }
 },
 "X2b-writer-claude-sonnet-fixed": {
  "n": 10,
  "outcomes": {
   "shipped": 10
  },
  "errors": 0,
  "first_pass_broke": 10,
  "shipped_break": 0,
  "repairs": 5.1,
  "seconds": 218,
  "p_max_seconds": 318,
  "usd_est": 0.1224,
  "quiz_shown": 34,
  "degradations": {},
  "models": {
   "gemini-3.7-flash": [
    31166,
    10482,
    30
   ],
   "IFM/K2-Horizon-375B-A23B": [
    174375,
    202711,
    221
   ],
   "nova-2-lite": [
    3471,
    8450,
    10
   ],
   "claude-sonnet-4.6": [
    114189,
    43156,
    173
   ],
   "claude-haiku": [
    19777,
    7686,
    16
   ]
  }
 },
 "X3-judge-ensemble": {
  "n": 10,
  "outcomes": {
   "shipped": 10
  },
  "errors": 0,
  "first_pass_broke": 9,
  "shipped_break": 0,
  "repairs": 3.6,
  "seconds": 241,
  "p_max_seconds": 440,
  "usd_est": 0.1375,
  "quiz_shown": 32,
  "degradations": {},
  "models": {
   "gemini-3.7-flash": [
    116195,
    33639,
    176
   ],
   "claude-sonnet-4.6": [
    159382,
    36268,
    196
   ],
   "IFM/K2-Horizon-375B-A23B": [
    150717,
    170777,
    200
   ],
   "nova-2-lite": [
    3475,
    8490,
    10
   ],
   "claude-haiku": [
    19862,
    8239,
    18
   ]
  }
 },
 "X4-no-judge": {
  "n": 10,
  "outcomes": {
   "shipped": 9,
   "shipped_with_notes": 1
  },
  "errors": 0,
  "first_pass_broke": 5,
  "shipped_break": 1,
  "repairs": 1.1,
  "seconds": 49,
  "p_max_seconds": 62,
  "usd_est": 0.0199,
  "quiz_shown": 34,
  "degradations": {},
  "models": {
   "gemini-3.7-flash": [
    82288,
    24138,
    121
   ],
   "nova-2-lite": [
    3843,
    8960,
    11
   ],
   "claude-haiku": [
    17240,
    7400,
    16
   ]
  }
 },
 "X5-repairs-0": {
  "n": 10,
  "outcomes": {
   "shipped": 4,
   "shipped_with_notes": 6
  },
  "errors": 0,
  "first_pass_broke": 7,
  "shipped_break": 6,
  "repairs": 0.4,
  "seconds": 154,
  "p_max_seconds": 274,
  "usd_est": 0.0184,
  "quiz_shown": 37,
  "degradations": {},
  "models": {
   "gemini-3.7-flash": [
    82447,
    23129,
    120
   ],
   "IFM/K2-Horizon-375B-A23B": [
    117498,
    111122,
    149
   ],
   "nova-2-lite": [
    3829,
    9175,
    11
   ],
   "claude-haiku": [
    10881,
    6431,
    10
   ]
  }
 },
 "X6-repairs-4": {
  "n": 10,
  "outcomes": {
   "shipped": 10
  },
  "errors": 0,
  "first_pass_broke": 9,
  "shipped_break": 0,
  "repairs": 2.5,
  "seconds": 177,
  "p_max_seconds": 377,
  "usd_est": 0.0224,
  "quiz_shown": 34,
  "degradations": {},
  "models": {
   "gemini-3.7-flash": [
    103845,
    28865,
    156
   ],
   "IFM/K2-Horizon-375B-A23B": [
    135469,
    153574,
    177
   ],
   "nova-2-lite": [
    3465,
    8600,
    10
   ],
   "claude-haiku": [
    17377,
    7490,
    16
   ]
  }
 }
}
```
