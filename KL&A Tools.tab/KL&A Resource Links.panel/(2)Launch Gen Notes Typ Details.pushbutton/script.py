# -*- coding: utf-8 -*-
__title__ = "(2)Launch Gen Notes Typ Details"

import subprocess

STUDIO_URL = "studio://studio.bluebeam.com/665-447-452/"

subprocess.Popen(["cmd", "/c", "start", "", STUDIO_URL], shell=False)

##NOTES
#this script will open a new instance of bluebeam if you do not alaready have one open
#If you are already logged into a bluebeam session, it will boot you from that session and open the KL&A graphics standards session
#If you have multiple bluebeam instances open, the script will open the KL&A graphics standards session in the first instance you had open