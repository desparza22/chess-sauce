import click
from typing import Optional
from my_engine.uci import main as uci_main 
from my_engine.perf import main as perf_main
from my_engine.eval import main as eval_main


@click.group()
def cli():
    pass

@cli.command()
@click.argument('log', type=str)
def uci(log: str) -> None:
    uci_main(log)

@cli.command()
@click.option('--linear', is_flag=True, help="Scheme for ordering moves to search")
@click.argument('depth', type=int)
@click.argument('fens', type=str)
def perf(depth: int, fens: str, linear: bool) -> None:
    perf_main(depth, fens, linear)

@cli.command()
@click.argument('fens', type=str)
def eval(fens: str) -> None:
    eval_main(fens)

if __name__ == "__main__":
    cli()