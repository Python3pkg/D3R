#!/usr/bin/env python

__author__ = 'j5wagner'

import commands
import os
import glob
import logging
import time
import re 
import shutil 
from d3r.utilities.challenge_data import ChallengeData

logger = logging.getLogger(__name__)



class ProteinPrep(object):
    """Abstract class defining methods for a custom protein and ligand preparation solution
    for CELPP
    """



    # This prep script will be required to output files with the appropriate suffixes
    OUTPUT_PROTEIN_SUFFIX = '.pdb'

    def prepare_protein(self, protein_file, prepared_protein_file, info_dic={}):
        """Does not do any scientific preparation - Passes protein forward without any processing 
        """
        
        # Poor man's receptor splitting - Remove all HETATM and
        # CONECT lines
        #data = open(protein_file).readlines()
        #with open(prepared_protein_file,'wb') as of:
        #    for line in data:
        #        if (line[:6] == 'HETATM') or (line[:6] == 'CONECT'):
        #            continue
        #        else:
        #            of.write(line)
        
        shutil.copyfile(protein_file, prepared_protein_file)
        return True





    def run_scientific_protein_prep(self, challenge_data_path, pdb_protein_path, working_folder):
        abs_challenge_data_path = os.path.abspath(challenge_data_path)
        chal_data_obj = ChallengeData(abs_challenge_data_path)
        if not(chal_data_obj.is_valid_for_celpp()):
            logging.info('%s is not a valid CELPP challenge data directory. Unable to run protein prep.')
            return False
        week_chal_data_dict = chal_data_obj.get_targets()
        week_name = week_chal_data_dict.keys()[0]
        abs_week_path = os.path.join(abs_challenge_data_path, week_name)
        pot_target_dirs = week_chal_data_dict[week_name]
        os.chdir(working_folder)
        current_dir_layer_1 = os.getcwd()

        ## Get all potential target directories and candidates within
        valid_candidates = {}


        # Ensure that the directories are valid
        for pot_target_dir in pot_target_dirs:
            os.chdir(current_dir_layer_1)
            pot_target_id = os.path.basename(pot_target_dir.strip('/'))
            # Does it look like a pdb id?
            if len(pot_target_id) != 4:
                logging.info('Filtering potential target directories: %s is not 4 characters long. Skipping' %(pot_target_id))
                continue

            os.mkdir(pot_target_id)

            valid_candidates[pot_target_id] = []
            target_dir_path = os.path.join(abs_week_path, pot_target_id)


            center_file = os.path.join(target_dir_path,'center.txt')
            center_file_basename = os.path.basename(center_file)
            center_file_dest = os.path.join(pot_target_id, center_file_basename)
            shutil.copyfile(center_file, center_file_dest)


            # Copy in each valid candidate
            for candidate_file in glob.glob('%s/*-%s_*.pdb' %(target_dir_path, pot_target_id)):
                # The LMCSS ligand will be in a pdb file called something like celpp_week19_2016/1fcz/LMCSS-1fcz_1fcz-156-lig.pdb
                # We want to make sure we don't treat this like a receptor
                if 'lig.pdb' in candidate_file:
                    continue
                candidate_file_basename = os.path.basename(candidate_file)
                candidate_file_dest = os.path.join(pot_target_id,candidate_file_basename)
                shutil.copyfile(candidate_file, candidate_file_dest)
                #commands.getoutput('cp %s %s' %(candidate_file, pot_target_id))
                candidate_local_file = os.path.basename(candidate_file)
                valid_candidates[pot_target_id].append(candidate_local_file)

        for target_id in valid_candidates.keys():
            os.chdir(target_id)

            for candidate_filename in valid_candidates[target_id]:
                ## Parse the candidate name 
                ## Get the method type, target, and candidate info from the filename
                # for example, this will parse 'hiResApo-5hib_2eb2_docked.mol' into [('hiResApo', '5hib', '2eb2')]

                parsed_name = re.findall('([a-zA-Z0-9]+)-([a-zA-Z0-9]+)_([a-zA-Z0-9]+)-?([a-zA-Z0-9]*).pdb', candidate_filename)
                if len(parsed_name) != 1:
                    logging.info('Failed to parse docked structure name "%s". Parsing yielded %r' %(candidate_filename, parsed_name))
                    continue
                candidate_structure_type = parsed_name[0][0]
                candidate_structure_target = parsed_name[0][1]
                candidate_structure_candidate = parsed_name[0][2]
                candidate_structure_ligand = parsed_name[0][2]

                # Split the complex 
                candidate_prefix = '%s-%s_%s' %(candidate_structure_type,
                                                candidate_structure_target,
                                                candidate_structure_candidate)

                prepared_protein_file = "%s_prepared%s" %(candidate_prefix, ProteinPrep.OUTPUT_PROTEIN_SUFFIX)

                preparation_result = self.prepare_protein(candidate_filename, prepared_protein_file)
                if preparation_result == False:
                    logging.info("Unable to prepare this protein:%s"%(candidate_filename))
                    continue
                if not(os.path.exists(prepared_protein_file)):
                    logging.info('Expected output file %s does not exist. Assuming that protein prep failed. Skipping candidate %s' %(prepared_protein_file, candidate_prefix))
                    continue
                if os.path.getsize(prepared_protein_file)==0:
                    logging.info('Expected output file %s has size 0. Assuming that protein prep failed. Skipping candidate %s' %(prepared_protein_file, candidate_prefix))
                    continue

                                 
                #convert into pdb format
                logging.info("Successfully prepared this protein:%s"%(prepared_protein_file))


            os.chdir(current_dir_layer_1)

