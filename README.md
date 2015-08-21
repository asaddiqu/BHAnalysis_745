# BHAnalysis
##1)CMSSW VERSION
-------------
CMSSW_7_4_5 version adopted becausue photon/electron IDs are implemented with this version.
##2) Required packages 
-----------------
for photon/electron IDs, do the followings:
```
cmsrel CMSSW_7_4_5
cd CMSSW_7_4_5/src
cmsenv
scram b -j 10  
```
##3) Reference Twikis for IDS
---------------------------
Jet ID     : https://twiki.cern.ch/twiki/bin/view/CMS/TopJME  
Electron ID: https://twiki.cern.ch/twiki/bin/view/CMS/CutBasedElectronIdentificationRun2  
Photon ID  : https://twiki.cern.ch/twiki/bin/view/CMS/CutBasedPhotonIdentificationRun2  
Muon ID    : https://twiki.cern.ch/twiki/bin/view/CMS/TopMUO  
##4) In this  Ntuplizer
-----------------------
###All the Objects IDs Applied:
Jets(loose), Electron and Photon (medium), Muon (tight)
###NoHFMET applied:
In the python "maketuples_jec(nojec)_cfg.py" files
###JEC applied:
Also in the python files. 
