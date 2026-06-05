# -*- coding: utf-8 -*-
__title__ = "Open\n KL&A Revit Standards Onenote Notebook"

import subprocess

onenote_uri = r"https://klaa.sharepoint.com/_layouts/15/Doc.aspx?sourcedoc={60930659-2718-4b7e-9a99-29568ed4af43}&action=edit&wd=target%28REVIT.one%7C73e89a03-1db3-4093-b85d-cf429fc0ed08%2F%E2%9E%A4%E2%9E%A4TABLE%20OF%20CONTENTS%20-%20START%20HERE%7C37e81031-6529-4a35-8546-95006986133f%2F%29&wdorigin=NavigationUrl"

subprocess.Popen(['cmd', '/c', 'start', '', onenote_uri], shell=False)

##NOTES