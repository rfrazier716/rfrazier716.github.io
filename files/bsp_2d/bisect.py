def bisect(segments: np.ndarray, line: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:

    single_segment = segments.ndim == 2
    if single_segment:
        segments = segments[np.newaxis, ...]

    segment_start = segments[..., 0, :]
    segment_end = segments[..., 1, :]

    v0 = segment_end - segment_start
    v1 = line[1] - line[0]

    # need to solve for the intersection equation, first find the numerator and denominator

    numerator = np.cross((line[0] - segment_start), v1)
    denominator = np.cross(v0, v1)

    # if the denominator is zero the lines are parallel
    parallel = np.isclose(denominator, 0)
    not_parallel = np.logical_not(parallel)

    # the intersection time is the point along the line segment where the line bisects it
    intersection = numerator / (denominator + parallel)

    ahead = np.logical_or(numerator > 0, np.logical_and(np.isclose(numerator, 0), denominator < 0))
    behind = np.logical_or(numerator < 0, np.logical_and(np.isclose(numerator, 0), denominator > 0))

    # segments are colinear if they are parallel and the numerator is zero
    colinear = np.logical_and(parallel, np.isclose(numerator, 0))

    # bisected segments are segments that aren't parallel and t is in (0,1)
    bisected = np.logical_and(
        not_parallel,
        np.logical_and(intersection > 0, intersection < 1)
    )

    # bisected lines need to be split up into new segments that are ahead and behind, first separate out the bisected
    # doing this to all segments to avoid fancy indexing at first
    intersection_points = segment_start + intersection[..., np.newaxis] * v0
    l_segments = np.stack((segments[..., 0, :], intersection_points), axis=1)
    r_segments = np.stack((intersection_points, segments[..., 1, :]), axis=1)

    mask = numerator[..., np.newaxis, np.newaxis] > 0
    bisected_ahead = np.where(mask, l_segments, r_segments)[bisected]
    bisected_behind = np.where(np.logical_not(mask), l_segments, r_segments)[bisected]

    # need to return 3 sets of segments, those in front, those colinear, and those behind
    ahead_mask = np.logical_and(ahead, np.logical_not(bisected))
    behind_mask = np.logical_and(behind, np.logical_not(bisected))

    if bisected_ahead.size != 0:
        if np.any(ahead_mask):
            all_ahead = np.concatenate((segments[ahead_mask], bisected_ahead))
        else:
            all_ahead = bisected_ahead
    else:
        all_ahead = segments[ahead_mask]
    if bisected_behind.size != 0:
        if np.any(behind_mask):
            all_behind = np.concatenate((segments[behind_mask], bisected_behind))
        else:
            all_behind = bisected_behind
    else:
        all_behind = segments[behind_mask]

    all_colinear = segments[colinear]

    return all_ahead, all_behind, all_colinear