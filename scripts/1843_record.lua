capture_file                    =   "1"

--TODO: edit this path!!
SAVE_DATA_PATH = "C:\\Users\\ubci\\OneDrive\\Bureau\\COM304\\comm-proj-radar\\processing\\record\\" .. capture_file .. ".bin"

ar1.CaptureCardConfig_StartRecord(SAVE_DATA_PATH, 1)
ar1.StartFrame()

