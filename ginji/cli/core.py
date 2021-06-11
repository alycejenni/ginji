import click
import time
from ginji.config import config, logger
from ginji.inputs import MotionInput
from ginji.outputs import VideoOutput
from ginji.connectors import uploaders, notifiers
import os
from datetime import datetime as dt


click_context = {
    'help_option_names': ['-h', '--help']
    }


@click.group(invoke_without_command=False, context_settings=click_context)
@click.pass_context
def cli(ctx):
    """
    A command line interface for working with ginji. If only it were that easy working with the actual cat.
    Run 'ginji <cmd> -h' for help with each subcommand.
    """
    active_connectors = [k for k, v in config.connector_config.items() if v.get('active', True)]
    ctx.obj = {
        'connectors': [c() for c in (uploaders + notifiers) if c.config_name in active_connectors]
        }


@cli.command(short_help='Start motion detection.')
@click.option('--tidy/--no-tidy', default=True,
              help='Tidy up any files that haven\'t been uploaded yet before initialising the motion detection.')
@click.option('--interval', type=int, help='Attempt a tidy every n seconds. Optional.')
@click.pass_context
def motion(ctx, tidy, interval):
    motion_input = MotionInput()
    video_output = VideoOutput()
    motion_input.register_outputs(video_output)
    video_output.register_connectors(*ctx.obj.get('connectors', []))

    if tidy:
        video_output.tidy()

    motion_input.start()

    if interval is None:
        interval = 300
        interval_tidy = False
    else:
        interval_tidy = True
    while True:
        try:
            time.sleep(interval)
            if interval_tidy and not motion_input.value and not video_output.processing:
                video_output.tidy()
        except KeyboardInterrupt:
            click.echo('Exiting.')
            motion_input.save_bg()
            motion_input.stop()
            break


@cli.command(short_help='Manually initiate a tidy-up of the output folder.')
@click.option('--motioneye', is_flag=True, default=False)
@click.pass_context
def sweep(ctx, motioneye):
    video_output = VideoOutput()
    video_output.register_connectors(*ctx.obj.get('connectors', []))

    # move everything into the right place
    if motioneye:
        for root, _, files in os.walk(config.root):
            for f in files:
                if not f.endswith(video_output.filetype):
                    continue
                video_date = root.split('/')[-1]
                video_time = f.split(os.extsep)[0]
                try:
                    video_datetime = dt.strptime(f'{video_date} {video_time}', '%Y-%m-%d %H-%M-%S').timestamp()
                except:
                    continue
                new_fn = video_output.make_filename(video_datetime, 2)
                os.rename(os.path.join(root, f), new_fn)

    video_output.tidy()
