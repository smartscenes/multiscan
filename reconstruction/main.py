import os
import psutil
import hydra
import logging

from hydra.utils import get_original_cwd
from omegaconf import DictConfig

from reconstruction.scripts.reconstruct import Reconstruct
from reconstruction.scripts.bridge import Bridge, File

log = logging.getLogger('reconstruct')

def main_from_cfg(cfg : DictConfig):
    basename = os.path.basename(cfg.output.save_folder)
    if "%s" in cfg.output.mesh_filename:
        cfg.output.mesh_filename = cfg.output.mesh_filename % basename
    if "%s" in cfg.output.decimated_mesh_filename:
        cfg.output.decimated_mesh_filename = cfg.output.decimated_mesh_filename % basename
    if "%s" in cfg.output.mesh_alignment_filename:
        cfg.output.mesh_alignment_filename = cfg.output.mesh_alignment_filename % basename

    log.info(f'Output diectory set to {cfg.output.save_folder}')
    log.info(f'Output raw mesh will be saved to {cfg.output.mesh_filename}')
    log.info(f'Output decimated mesh will be saved to {cfg.output.decimated_mesh_filename}')
    log.info(f'Output mesh coordinate alignment file will be saved to {cfg.output.mesh_alignment_filename}')

    # set number of cpus to use
    pid = os.getpid()
    p = psutil.Process(pid)
    cpu_num = min(len(p.cpu_affinity()), cfg.settings.cpu_num)
    p.cpu_affinity(p.cpu_affinity()[0:cpu_num])

    log.info(f'{cpu_num} CPUs will be used in reconstruction')

    try:
        if cfg.settings.with_camera_poses:
            log.info('Start reconstruction with known camera poses')
            bridge = Bridge(cfg)
            if os.path.isdir(cfg.input.depth_stream):
                log.info('Reconstruction with decoded images')
                bridge.open_file(cfg.input.metadata_file, File.META)
                bridge.open_file(cfg.input.trajectory_file, File.POSE)
            else:
                log.info('Reconstruction with compressed streams')
                bridge.open_all()
            bridge.read_metadata()
        
            recon = Reconstruct(cfg, bridge)
            recon.run()

            bridge.close_all()
        else:
            log.info('Start multiway registration reconstruction')
            recon = Reconstruct(cfg)
            recon.run()
    except ValueError as e:
        raise e
    except IOError as e:
        raise e

    # reset affinity against all cpus
    all_cpus = list(range(psutil.cpu_count()))
    p.cpu_affinity(all_cpus)


@hydra.main(config_path="../config", config_name="config")
def main(cfg : DictConfig) -> None:
    cfg = cfg.reconstruction
    # parse inputs
    if not os.path.isabs(cfg.input.color_stream):
        cfg.input.color_stream = os.path.join(get_original_cwd(), cfg.input.color_stream)
    if not os.path.isabs(cfg.input.depth_stream):
        cfg.input.depth_stream = os.path.join(get_original_cwd(), cfg.input.depth_stream)
    if not os.path.isabs(cfg.input.confidence_stream):
        cfg.input.confidence_stream = os.path.join(get_original_cwd(), cfg.input.confidence_stream)
    if not os.path.isabs(cfg.input.metadata_file):
        cfg.input.metadata_file = os.path.join(get_original_cwd(), cfg.input.metadata_file)
    if not os.path.isabs(cfg.input.intrinsics_file):
        cfg.input.intrinsics_file = os.path.join(get_original_cwd(), cfg.input.intrinsics_file)
    if not os.path.isabs(cfg.input.trajectory_file):
        cfg.input.trajectory_file = os.path.join(get_original_cwd(), cfg.input.trajectory_file)

    # parse outputs
    cfg.output.save_folder = os.path.normpath(cfg.output.save_folder)
    if not os.path.isabs(cfg.output.save_folder):
        cfg.output.save_folder = os.path.join(get_original_cwd(), cfg.output.save_folder)
    
    main_from_cfg(cfg)

if __name__ == '__main__':
    main()
