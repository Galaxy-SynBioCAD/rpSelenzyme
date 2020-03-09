#!/usr/bin/env python3
"""
Created on September 21 2019

@author: Melchior du Lac
@description: rpSelenzyme REST entry script

"""

import logging
import tempfile
import json
import sys
import csv
sys.path.insert(0, '/home/selenzy/')
import Selenzy

## global parameter 
DATADIR = '/home/selenzy/data/'
pc = Selenzy.readData(DATADIR)

############## Cache ##############

uniprot_aaLenght = {}
with open(DATADIR+'sel_len.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    next(csv_reader)
    for row in csv_reader:
        uniprot_aaLenght[row[0].split('|')[1]] = row[1]

############## Tools ##############

#Empty to follow the rp tools writting convention

def singleReactionRule(reaction_smile,
                       host_taxonomy_id,
                       num_targets=50,
                       direction=0,
                       noMSA=True,
                       fp='RDK',
                       rxntype='smarts'):
    uniprotID_score = {}
    score = Selenzy.seqScore()
    with tempfile.TemporaryDirectory() as tmpOutputFolder:
        success, results = Selenzy.analyse(['-'+rxntype, reaction_smile], num_targets, DATADIR, tmpOutputFolder, 'tmp.csv', 0, host_taxonomy_id, pc=pc, NoMSA=noMSA)
        data = Selenzy.updateScore(tmpOutputFolder+'/tmp.csv', score)
        val = json.loads(data.to_json())
        if 'Seq. ID' in val and len(val['Seq. ID'])>0:
            for ix in sorted(val['Seq. ID'], key=lambda z: int(z)):
                uniprotID_score[val['Seq. ID'][ix]] = val['Score'][ix]
        else:
            raise ValueError
        return uniprotID_score


def singleSBML(rpsbml,
               host_taxonomy_id=83333,
               pathway_id='rp_pathway',
               num_targets=50,
               direction=0,
               noMSA=True,
               fp='RDK',
               rxntype='smarts',
               min_aa_length=100):
    for reac_id in rpsbml.readRPpathwayIDs(pathway_id):
        reac = rpsbml.model.getReaction(reac_id)
        brs_reac = rpsbml.readBRSYNTHAnnotation(reac.getAnnotation())
        if brs_reac['smiles']:
            try:
                uniprotID_score = singleReactionRule(brs_reac['smiles'], host_taxonomy_id, num_targets, direction, noMSA, fp, rxntype)
                uniprotID_score_restricted = {}
                for uniprot in uniprotID_score:
                    if uniprotID_score[uniprot]>int(min_aa_length):
                        uniprotID_score_restricted[uniprot] = uniprotID_score[uniprot]
                '''
                xref = {'uniprot': [i for i in uniprotID_score]}
                rpsbml.addUpdateMIRIAM(reac, 'reaction', xref)
                rpsbml.addUpdateBRSynth(reac, 'selenzyme', uniprotID_score, None, False, True, True)
                '''
                xref = {'uniprot': [i for i in uniprotID_score_restricted]}
                rpsbml.addUpdateMIRIAM(reac, 'reaction', xref)
                rpsbml.addUpdateBRSynth(reac, 'selenzyme', uniprotID_score_restricted, None, False, True, True)
            except ValueError:
                logging.warning('Problem with retreiving the selenzyme information for model '+str(rpsbml.model.getId()))
                return False
        else:
            logging.warning('Cannot retreive the reaction rule of model '+str(rpsbml.model.getId()))
            return False
    return True



