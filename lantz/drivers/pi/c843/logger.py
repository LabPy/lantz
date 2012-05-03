import logging
import tempfile
import functools
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

if __debug__:
    def logged(function):
        #@functools.wraps(function)
        def decorator(*args, **kwargs):
            #logger.info("calling {} with args {}".format(f.__name__, args[1:]))
            log = "called: " + function.__name__ + "("
            log += ", ".join(["{0!r}".format(a) for a in args[1:]] +
                        ["{0!s}={1!r}".format(k, v) for k, v in kwargs.items()])
            result = exception = None
            try:
                result = function(*args, **kwargs)
                log += (") -> " + str(result)) 
                logger.info(log)
                return result
            except Exception as err:
                exception = err
                log += (") -> " + ") {0}: {1}".format(type(exception),
                        exception))
                logger.error(log)
            #finally:
                #log += ((") -> " + str(result)) if exception is None
                        #else ") {0}: {1}".format(type(exception),
                        #exception))
                #logger.error(log)
                #logger.debug(log)
                #if exception is not None:
                    #raise exception
        return decorator

else:
    def logged(function):
        return function
