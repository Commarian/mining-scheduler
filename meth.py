def convert_time(duration, from_unit, to_unit):
    """
    Convert time between seconds, hours, and days.

    Parameters:
    - duration: The time duration to convert.
    - from_unit: The unit of the input duration ('seconds', 'hours', 'days').
    - to_unit: The desired unit for the output ('seconds', 'hours', 'days').

    Returns:
    The converted time duration.
    """
    conversion_factors = {
        ('seconds', 'hours'): 1 / 3600,
        ('seconds', 'days'): 1 / (3600 * 24),
        ('hours', 'seconds'): 3600,
        ('hours', 'days'): 1 / 24,
        ('days', 'seconds'): 3600 * 24,
        ('days', 'hours'): 24,
    }

    if from_unit == to_unit:
        return int(duration)

    conversion_factor = conversion_factors.get((from_unit, to_unit))
    if conversion_factor is not None:
        return int(duration * conversion_factor)
    else:
        raise ValueError(f"Conversion from {from_unit} to {to_unit} is not supported.")