import numpy as np
from scipy.spatial.transform import Rotation as R


# compute rotation matrix from two vectors
def rotation_from2vectors(source, target):
    norm_source = source / np.linalg.norm(source)
    norm_target = target / np.linalg.norm(target)
    if np.linalg.norm(np.cross(norm_source, norm_target)) <= np.finfo(float).eps:
        vec = norm_source
    else:
        vec = np.cross(norm_source, norm_target)
    rot = np.arccos(np.dot(norm_source, norm_target))
    r = R.from_rotvec(rot * vec)

    return r.as_matrix()


# compute intersection point of two lines
# trigonometry, law of sines: a/sin(A) = b/sin(B)
def intersect_lines(s0, d0, s1, d1):
    """
    s0, s1: 2D coordinates of a point
    d0, d1: direction vector determines the direction a line
    """
    sin_a = np.cross(d0, d1)
    vec_s = s1 - s0
    t = np.cross(vec_s, d1) / sin_a

    return s0 + t * d0
