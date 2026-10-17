"""A descriptive, equal-weight summary of choices in the three risk tasks."""

RISK_LEVELS = (
    'risk_type_very_averse',
    'risk_type_moderately_averse',
    'risk_type_slightly_averse',
    'risk_type_neutral',
    'risk_type_moderately_seeking',
    'risk_type_very_seeking',
)
PROFILE_LEVELS = (
    'overall_profile_very_cautious',
    'overall_profile_somewhat_cautious',
    'overall_profile_middle',
    'overall_profile_somewhat_willing',
    'overall_profile_very_willing',
)


def overall_choice_profile(mpl_type, bret_type, investment_type):
    """Return (level key, task count) for an equal-weight descriptive average.

    Ambiguous task choices contribute no score. At least two interpretable
    tasks are needed for a summary.
    """
    level_values = {
        'risk_type_very_averse': 0,
        'risk_type_moderately_averse': 1,
        'risk_type_slightly_averse': 1.5,
        'risk_type_neutral': 2,
        'risk_type_moderately_seeking': 3,
        'risk_type_very_seeking': 4,
    }
    levels = [
        level_values[key]
        for key in (mpl_type, bret_type, investment_type)
        if key in level_values
    ]
    if len(levels) < 2:
        return None, len(levels)
    average = sum(levels) / len(levels)
    return PROFILE_LEVELS[int(average + 0.5)], len(levels)
