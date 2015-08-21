import FWCore.ParameterSet.Config as cms 

process = cms.Process('ANA')

process.load('Configuration.EventContent.EventContent_cff')
process.load('Configuration.StandardSequences.Services_cff')
process.load('Configuration.StandardSequences.Geometry_cff')
process.load('Configuration.StandardSequences.MagneticField_38T_cff')
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')

# Message Logger settings
process.load("FWCore.MessageService.MessageLogger_cfi")
process.MessageLogger.destinations = ['cout', 'cerr']
process.MessageLogger.cerr.FwkReport.reportEvery = 1

# Set the process options -- Display summary at the end, enable unscheduled execution
process.options = cms.untracked.PSet(
    allowUnscheduled = cms.untracked.bool(True),
    wantSummary = cms.untracked.bool(True)
)

# HCAL filter (next 2 lines) added on 24 July 2015
process.load('CommonTools.RecoAlgos.HBHENoiseFilterResultProducer_cfi')
process.HBHENoiseFilterResultProducer.minZeros = cms.int32(99999)

process.ApplyBaselineHBHENoiseFilter = cms.EDFilter('BooleanFlagFilter',
   inputLabel = cms.InputTag('HBHENoiseFilterResultProducer','HBHENoiseFilterResult'),
   reverseDecision = cms.bool(False)
)
# How many events to process
process.maxEvents = cms.untracked.PSet(input = cms.untracked.int32(20))
#configurable options ==============================================
runOnData=True #data/MC switch
usePrivateSQlite=True #use external JECs (sqlite file)
useHFCandidates=False #create an additionnal NoHF slimmed MET collection if the option is set to false
applyResiduals=True #application of residual corrections. Have to be set to True once the 13 TeV residual 
#corrections are available. False to be kept meanwhile. Can be kept to False later for private tests or 
#for analysis checks and developments (not the official recommendation!).
#===================================================================
#from Configuration.StandardSequences.FrontierConditions_GlobalTag_condDBv2_cff import *
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_condDBv2_cff')
from Configuration.AlCa.GlobalTag_condDBv2 import GlobalTag

if runOnData:
  process.GlobalTag.globaltag = '74X_dataRun2_Prompt_v1'
else:
  #process.GlobalTag.globaltag = 'auto:run2_mc'
  process.GlobalTag.globaltag = 'MCRUN2_74_V9'
if usePrivateSQlite:
  from CondCore.DBCommon.CondDBSetup_cfi import *
  import os
  if runOnData:
    jecfile="Summer15_50nsV4_DATA"
  else:
    jecfile="Summer15_50nsV4_MC"
  dBFile = os.path.expandvars("$CMSSW_BASE/src/BH_CMS2015/BHAnalysis-master/jec/"+jecfile+".db")
  process.jec = cms.ESSource("PoolDBESSource",CondDBSetup,
    connect = cms.string( "sqlite_file://"+dBFile ),
    toGet =  cms.VPSet(
    cms.PSet(
      record = cms.string("JetCorrectionsRecord"),
      tag = cms.string("JetCorrectorParametersCollection_"+jecfile+"_AK4PF"),
      label= cms.untracked.string("AK4PF")
      ),
    cms.PSet(
      record = cms.string("JetCorrectionsRecord"),
      tag = cms.string("JetCorrectorParametersCollection_"+jecfile+"_AK4PFchs"),
      label= cms.untracked.string("AK4PFchs")
      ),
    )
    )
process.es_prefer_jec = cms.ESPrefer("PoolDBESSource",'jec')
#-----------------For JEC-----------------
process.load("PhysicsTools.PatAlgos.producersLayer1.jetUpdater_cff")
from PhysicsTools.PatAlgos.producersLayer1.jetUpdater_cff import patJetCorrFactorsUpdated
process.patJetCorrFactorsReapplyJEC = process.patJetCorrFactorsUpdated.clone(
  src = cms.InputTag("slimmedJets"),
  levels = ['L1FastJet', 'L2Relative', 'L3Absolute'],
  payload = 'AK4PFchs' ) # Make sure to choose the appropriate levels and payload here!

from PhysicsTools.PatAlgos.producersLayer1.jetUpdater_cff import patJetsUpdated
process.patJetsReapplyJEC = process.patJetsUpdated.clone(
  jetSource = cms.InputTag("slimmedJets"),
  jetCorrFactorsSource = cms.VInputTag(cms.InputTag("patJetCorrFactorsReapplyJEC"))
  )
process.JEC = cms.Sequence( process.patJetCorrFactorsReapplyJEC + process. patJetsReapplyJEC )
#-------------------------------------------
#uncertainty file
jecUncertaintyFile="BH_CMS2015/BHAnalysis-master/jec/Summer15_50nsV4_DATA_UncertaintySources_AK4PFchs.txt"

process.load('FWCore.MessageService.MessageLogger_cfi')
process.MessageLogger.cerr.FwkReport.reportEvery = 1

process.TFileService=cms.Service("TFileService",
        fileName=cms.string("ntuple_output.root"),
        closeFileFast = cms.untracked.bool(True)
)

process.out = cms.OutputModule('PoolOutputModule',
  compressionLevel = cms.untracked.int32(4),
  compressionAlgorithm = cms.untracked.string('LZMA'),
  eventAutoFlushCompressedSize = cms.untracked.int32(15728640),
  fileName = cms.untracked.string('edm_output.root'),
  outputCommands = cms.untracked.vstring('keep *'),
  dataset = cms.untracked.PSet(
          filterName = cms.untracked.string(''),
          dataTier = cms.untracked.string('')
          ),
  dropMetaData = cms.untracked.string('ALL'),
  fastCloning = cms.untracked.bool(False),
  overrideInputFileSplitLevels = cms.untracked.bool(True)
)

# Define the input source
if runOnData:
  fname = 'root://eoscms.cern.ch//store/data/Run2015B/JetHT/MINIAOD/PromptReco-v1/000/251/252/00000/263D331F-AF27-E511-969B-02163E012627.root'
else:
  fname = 'root://eoscms.cern.ch//store/mc/RunIISpring15DR74/DYJetsToLL_M-50_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8/MINIAODSIM/Asympt50ns_MCRUN2_74_V9A-v2/60000/001C7571-0511-E511-9B8E-549F35AE4FAF.root'
# Define the input source
process.source = cms.Source("PoolSource",fileNames = cms.untracked.vstring([ fname ])
)

### ---------------------------------------------------------------------------
### Removing the HF from the MET computation
### ---------------------------------------------------------------------------
if not useHFCandidates:
  process.noHFCands = cms.EDFilter("CandPtrSelector",
  src=cms.InputTag("packedPFCandidates"),
  cut=cms.string("abs(pdgId)!=1 && abs(pdgId)!=2 && abs(eta)<3.0")
  )
#jets are rebuilt from those candidates by the tools, no need to do anything else
### =================================================================================
from PhysicsTools.PatUtils.tools.runMETCorrectionsAndUncertainties import runMetCorAndUncFromMiniAOD

#default configuration for miniAOD reprocessing, change the isData flag to run on data
#for a full met computation, remove the pfCandColl input
runMetCorAndUncFromMiniAOD(process,
  isData=runOnData,
  jecUncFile=jecUncertaintyFile
  )

if not useHFCandidates:
  runMetCorAndUncFromMiniAOD(process,
  isData=runOnData,
  pfCandColl=cms.InputTag("noHFCands"),
  jecUncFile=jecUncertaintyFile,
  postfix="NoHF"
  )
### -------------------------------------------------------------------
### the lines below remove the L2L3 residual corrections when processing data
### -------------------------------------------------------------------
if not applyResiduals:
  process.patPFMetT1T2Corr.jetCorrLabelRes = cms.InputTag("L3Absolute")
  process.patPFMetT1T2SmearCorr.jetCorrLabelRes = cms.InputTag("L3Absolute")
  process.patPFMetT2Corr.jetCorrLabelRes = cms.InputTag("L3Absolute")
  process.patPFMetT2SmearCorr.jetCorrLabelRes = cms.InputTag("L3Absolute")
  process.shiftedPatJetEnDown.jetCorrLabelUpToL3Res = cms.InputTag("ak4PFCHSL1FastL2L3Corrector")
  process.shiftedPatJetEnUp.jetCorrLabelUpToL3Res = cms.InputTag("ak4PFCHSL1FastL2L3Corrector")
  if not useHFCandidates:
    process.patPFMetT1T2CorrNoHF.jetCorrLabelRes = cms.InputTag("L3Absolute")
    process.patPFMetT1T2SmearCorrNoHF.jetCorrLabelRes = cms.InputTag("L3Absolute")
    process.patPFMetT2CorrNoHF.jetCorrLabelRes = cms.InputTag("L3Absolute")
    process.patPFMetT2SmearCorrNoHF.jetCorrLabelRes = cms.InputTag("L3Absolute")
    process.shiftedPatJetEnDownNoHF.jetCorrLabelUpToL3Res = cms.InputTag("ak4PFCHSL1FastL2L3Corrector")
    process.shiftedPatJetEnUpNoHF.jetCorrLabelUpToL3Res = cms.InputTag("ak4PFCHSL1FastL2L3Corrector")
### ------------------------------------------------------------------
#luminosity
import FWCore.ParameterSet.Config as cms
import FWCore.PythonUtilities.LumiList as LumiList
#process.source.lumisToProcess = LumiList.LumiList(filename = '/afs/cern.ch/work/a/asaddiqu/BH_CMS/CMSSW_7_4_5/src/BH_CMS2015/BHAnalysis-master/JSON_CRAB/golden_246908-251883_13TeV_40pb.txt').getVLuminosityBlockRange()

#input file
#import FWCore.Utilities.FileUtils as FileUtils
#files2015data = FileUtils.loadListFromFile ('files.txt') 
#readFiles = cms.untracked.vstring( *files2015data )
#process.source.fileNames = readFiles

# Set up electron ID (VID framework)
from PhysicsTools.SelectorUtils.tools.vid_id_tools import *
# turn on VID producer, indicate data format  to be
# DataFormat.AOD or DataFormat.MiniAOD, as appropriate 
dataFormat = DataFormat.MiniAOD

switchOnVIDElectronIdProducer(process, dataFormat)

# define which IDs we want to produce
my_id_modules_el = ['RecoEgamma.ElectronIdentification.Identification.cutBasedElectronID_PHYS14_PU20bx25_V2_cff']

#add them to the VID producer
for idmod in my_id_modules_el:
    setupAllVIDIdsInModule(process,idmod,setupVIDElectronSelection)

switchOnVIDPhotonIdProducer(process, dataFormat)
my_id_modules_ph = ['RecoEgamma.PhotonIdentification.Identification.cutBasedPhotonID_PHYS14_PU20bx25_V2_cff']

#add them to the VID producer
for idmod in my_id_modules_ph:
    setupAllVIDIdsInModule(process,idmod,setupVIDPhotonSelection)

process.bhana = cms.EDAnalyzer('BHAnalyzerTLBSM',
  beamSpot = cms.InputTag('offlineBeamSpot'),
  electronTag = cms.InputTag("slimmedElectrons"),
  muonTag = cms.untracked.InputTag("slimmedMuons"),
  jetTag = cms.untracked.InputTag("slimmedJets"),
  tauTag = cms.untracked.InputTag("slimmedTaus"),
  metTag = cms.untracked.InputTag("slimmedMETsNoHF"),
  photonTag = cms.InputTag("slimmedPhotons"),
  rho_lable    = cms.untracked.InputTag("fixedGridRhoFastjetAll"),
  ebRecHitTag = cms.untracked.InputTag("reducedEgamma", "reducedEBRecHits"),
  eeRecHitTag = cms.untracked.InputTag("reducedEgamma", "reducedEERecHits"),
  primaryVertex = cms.untracked.InputTag("offlineSlimmedPrimaryVertices"),
  triggerTag = cms.untracked.InputTag("TriggerResults","","HLT"),
  prescales = cms.InputTag("patTrigger"), 
  verticesMiniAOD     = cms.InputTag("offlineSlimmedPrimaryVertices"),
  conversionsMiniAOD  = cms.InputTag('reducedEgamma:reducedConversions'),

  eleVetoIdMap   = cms.InputTag("egmGsfElectronIDs:cutBasedElectronID-PHYS14-PU20bx25-V2-standalone-veto"),
  eleLooseIdMap  = cms.InputTag("egmGsfElectronIDs:cutBasedElectronID-PHYS14-PU20bx25-V2-standalone-loose"),
  eleMediumIdMap = cms.InputTag("egmGsfElectronIDs:cutBasedElectronID-PHYS14-PU20bx25-V2-standalone-medium"),
  eleTightIdMap  = cms.InputTag("egmGsfElectronIDs:cutBasedElectronID-PHYS14-PU20bx25-V2-standalone-tight"),
 
  phoLooseIdMap = cms.InputTag("egmPhotonIDs:cutBasedPhotonID-PHYS14-PU20bx25-V2-standalone-loose"),
  phoMediumIdMap = cms.InputTag("egmPhotonIDs:cutBasedPhotonID-PHYS14-PU20bx25-V2-standalone-medium"),
  phoTightIdMap = cms.InputTag("egmPhotonIDs:cutBasedPhotonID-PHYS14-PU20bx25-V2-standalone-tight"),
 
  MCLabel = cms.untracked.bool(True),                               
  DEBUG = cms.untracked.bool(False)                               
)


process.p = cms.Path(process.HBHENoiseFilterResultProducer* #produces HBHE bools
	process.ApplyBaselineHBHENoiseFilter*  #reject events based 
	(process.egmPhotonIDSequence+process.egmGsfElectronIDSequence) * process.bhana)
process.p +=cms.Sequence(process.JEC)
