import ctypes as ct

cam = ct.WinDLL("MUCam32.dll")

camlist = (ct.c_void_p*10)()
#hndl = ct.c_void_p()
hndl = ct.c_void_p(0)

hndl = cam.MUCam_findCamera()
print(hndl)
print(type(hndl))

hndl = ct.c_void_p(hndl)


print(hndl)
print(type(hndl))

cam.MUCam_openCamera(hndl)
camlist[0] = hndl
print(camlist[0])

cam.MUCam_releaseCamera(camlist[0])


