function struct_level = create_levelParameters(TR, events, onset, duration)
    struct_level.timing_units = 'secs';
    struct_level.timing_RT = TR;
    struct_level.conditionEvent = events;
    struct_level.conditionOnset = onset;
    struct_level.conditionDuration = duration;
end
