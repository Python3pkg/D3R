#!/usr/bin/evn python

import commands
import os
import glob
import logging
import time

logger = logging.getLogger()
logging.basicConfig( format  = '%(asctime)s: %(message)s', datefmt = '%m/%d/%y %I:%M:%S', filename = 'final.log', filemode = 'w', level   = logging.INFO )


def grid (grid_center, prep_pro):
    protein_name = prep_pro.split(".")[0]
    out_grid = protein_name + ".zip"
    grid_in  = protein_name +  "_grid.in"
    grid_1 = "GRID_CENTER \t %s \n"%grid_center
    grid_2 = "GRIDFILE \t %s \n"%out_grid
    grid_3 = "INNERBOX \t 10, 10, 10 \n"
    grid_4 = "OUTERBOX \t 30, 30, 30 \n"
    grid_5 = "RECEP_FILE \t %s \n"%prep_pro
    f = open (grid_in, "w")
    for grid_line in (grid_1, grid_2, grid_3, grid_4, grid_5):
        f.writelines(grid_line)
    f.close()
    commands.getoutput("$SCHRODINGER/glide -WAIT %s"%grid_in)
    if os.path.isfile(out_grid):
        return out_grid
    else:
        return False

def dock(ligand_file, out_grid, protein_title):
    dock_in = protein_title + "_dock.in"
    dock_1 = "GRIDFILE \t %s \n"%out_grid
    dock_2 = "LIGANDFILE \t %s \n"%ligand_file
    dock_3 = "POSTDOCK_XP_DELE \t 0.5 \n"
    dock_4 = "PRECISION \t XP \n"
    dock_5 = "EXPANDED_SAMPLING \t True \n"
    dock_6 = "POSES_PER_LIG \t 10 \n"
    dock_7 = "WRITE_XP_DESC \t False \n"
    f = open(dock_in, "w")
    for dock_line in (dock_1, dock_2, dock_3, dock_4, dock_5, dock_6, dock_7):
        f.writelines(dock_line)
    f.close()
    out_dock_file = protein_title + "_dock_pv.maegz"
    commands.getoutput("$SCHRODINGER/glide -WAIT %s"%dock_in)
    return out_dock_file

def main_glide (stage_3_result, stage_4_working, update= True):
    os.chdir(stage_4_working)
    current_dir = os.getcwd()
    dockable_paths = []
    for all_pdb_path in os.walk(stage_3_result):
        if all_pdb_path[0] != stage_3_result:
            dockable_paths.append(all_pdb_path[0])

    for dockable_path in dockable_paths:
        commands.getoutput("cp -r %s %s" %(dockable_path, stage_4_working))
        target_name = os.path.basename(dockable_path)
        os.chdir(target_name)
        current_dir_layer_2 = os.getcwd()
        ##################
        #Do the docking here
        
        #1, get the center
        try:
            grid_center = open("center.txt","r").readlines()[0]
            logging.info("=============Start working on this case:%s=========="%target_name)
        except:
            logging.info("Fatal error: Unable to find the center file for this case %s"%target_name)
            os.chdir(current_dir)
            continue
            
        # Get the candidate protein names in this directory
        candidate_proteins = glob.glob('./*-????_????_prepared.maegz')
        logging.info('Found candidates %r' %(candidate_proteins))

        # Get the ligand names in this directory
        ligand_maes = glob.glob('lig_*_prepped.mae')
        ligand_maes = [i for i in ligand_maes if not "unprep" in i]
        if len(ligand_maes) == 0:
            logging.info('No ligand files found for target %s. Skipping.' %(dockable_path))
            os.chdir(current_dir)
            continue
        if len(ligand_maes) > 1:
            logging.info('Multiple ligand files found for target %s (found ligands %r). The workflow currently should only be sending one ligand. Skipping. ' %(dockable_path, ligand_maes))
            os.chdir(current_dir)
            continue
            
        #for possible_protein in ("largest.maegz", "smallest.maegz", "holo.maegz", "apo.maegz"):
        for candidate_protein in candidate_proteins:
            candidate_prefix = candidate_protein.replace('.maegz','')

            #if os.path.isfile(candidate_protein):
            logging.info( "Working on this receptor: %s"%candidate_prefix )
            if not os.path.isdir(candidate_prefix):
                os.mkdir(candidate_prefix)
            os.chdir(candidate_prefix)
            ##################
            #do docking inside
            commands.getoutput("cp ../%s ."%candidate_protein)

            #generate grid
            logging.info("Trying to get the grid file...")
            if update: 
                out_grid = grid(grid_center, candidate_protein) 
                #time.sleep(200)
            else:
                #check if there is old grid
                out_grid = candidate_prefix + ".zip"
                if not os.path.isfile(out_grid):
                    out_grid = grid(grid_center, candidate_protein)
                    #time.sleep(200)
            logging.info("Finished grid generation...")
            
            ## Dock each ligand
            for ligand_mae in ligand_maes:
                commands.getoutput("cp ../%s ." %(ligand_mae))
                logging.info("Trying to dock...")
                if update:
                    out_dock = dock("ligand.mae", out_grid, candidate_prefix)
                else:
                    out_dock = candidate_prefix + "_dock_pv.maegz"
                    if not os.path.isfile(out_dock):
                        out_dock = dock(ligand_mae, out_grid, candidate_prefix)
                logging.info("Finished docking, beginning post-docking file conversion")
                
                # Split the results into receptor and poses
                intermediate_prefix = '%s_postdocking' %(candidate_prefix)
                receptorMae = intermediate_prefix+'_receptor1.mae'
            
            
                ## Split into a receptor mae file and one ligand mae for each pose
                commands.getoutput('$SCHRODINGER/run split_structure.py -m ligand -many_files %s %s.mae' %(out_dock, intermediate_prefix))
            
                ## Convert the receptor mae into pdb
                # This pdb is one of the final outputs from docking
                receptorPdb = intermediate_prefix+'_receptor1.pdb'
                commands.getoutput('/opt/schrodinger2015-3/utilities/structconvert %s %s' %(receptorMae, receptorPdb))
            
                ## Convert the ligand maes into mols
                docked_ligand_maes = glob.glob('./%s_ligand?.mae' %(intermediate_prefix))
                for docked_ligand_mae in docked_ligand_maes:
                    docked_ligand_mol = ligand_mae.replace('.mae','.mol') 
                    commands.getoutput('/opt/schrodinger2015-3/utilities/structconvert %s %s' %(docked_ligand_mae, docked_ligand_mol))

            # Copy the top-ranked ligand mol to be one of the final outputs from this step
            top_ligand_mol = intermediate_prefix+'_ligand1.mol'
            output_ligand_mol = '%s_docked.mol' %(candidate_prefix)
            commands.getoutput('cp %s %s' %(top_ligand_mol, output_ligand_mol))
      
            ##################
            os.chdir(current_dir_layer_2)
        os.chdir(current_dir)
        ##################

if ("__main__") == (__name__):
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-s", "--structuredir", metavar="PATH", help = "PATH where we can find the proteinligprep output")
    parser.add_argument("-o", "--outdir", metavar = "PATH", help = "PATH where we will put the docking output")
    parser.add_argument("-u", "--update", action = "store_true",  help = "Update the docking result", default = False) 
    logger = logging.getLogger()
    logging.basicConfig( format  = '%(asctime)s: %(message)s', datefmt = '%m/%d/%y %I:%M:%S', filename = 'final.log', filemode = 'w', level = logging.INFO )
    opt = parser.parse_args()
    proteinligprep_dir = opt.structuredir
    dock_result_dir = opt.outdir
    update = opt.update
    #running under this dir
    running_dir = os.getcwd()
    main_glide(proteinligprep_dir, dock_result_dir, update = update)
    #move the final log file to the result dir
    log_file_path = os.path.join(running_dir, 'final.log')
    commands.getoutput("mv %s %s"%(log_file_path, dock_result_dir))
