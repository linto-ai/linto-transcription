import os
import hashlib
import subprocess

__all__ = ["fileHash", "requestlog"]

def fileHash(f):
    return hashlib.md5(f).hexdigest()

def requestlog(logger, origin, param, hashed, result_cached):
    logger.info("""Request received:\n
                Origin: {}\n 
                Hash: {}\n
                Param: {}\n
                Result_cached: {}""".format(
                    origin,
                    hashed,
                    param,
                    result_cached
                ))
