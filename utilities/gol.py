def __init(opt_v,polyl,optl):
    global opt_vector
    global now_id
    global polylen
    global optlen
    now_id = 1
    opt_vector = opt_v
    polylen = polyl
    optlen = optl
def set_value(arg, value):
    opt_vector[arg] = value
def reset_all_value(opt_v):
    opt_vector = opt_v
def get_value(arg):
    return opt_vector[arg]
def get_len():
    return len(opt_vector) - optlen
def get_all():
    return opt_vector
def get_now_id():
    return now_id
def set_now_id(value):
    now_id = value
def get_polylen():
    return polylen

def get_optlen():
    return optlen