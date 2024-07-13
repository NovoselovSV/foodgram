import inspect
import sys

MODELS_MODULE_NAME = 'core.models'


def get_name_model_dict():
    return {cls_name: cls_obj
            for cls_name, cls_obj
            in inspect.getmembers(sys.modules[MODELS_MODULE_NAME],
                                  inspect.isclass)
            if cls_obj.__module__ == MODELS_MODULE_NAME}
