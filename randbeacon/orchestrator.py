# -*- coding: utf-8 -*-
from input_collection import SimpleTCPInputCollector, UrandomInputCollector
from input_processing import MerkleTreeInputProcessor
from computation import SlothComputation

input_collectors = [SimpleTCPInputCollector(), UrandomInputCollector()]

input_processor = MerkleTreeInputProcessor()

computation = SlothComputation(sloth_iterations=1000)

INP_PERIOD = 10

def main():
    import threading

    collector_threads = [threading.Thread(target=c.collect, kwargs={'duration': INP_PERIOD}) for c in input_collectors]

    print("{:=^80}".format(" COLLECTING INPUT "))
    for thread in collector_threads:
        thread.start()

    for thread in collector_threads:
        thread.join()

    print("{:=^80}".format(" PROCESSING INPUT "))
    from itertools import chain
    # input_data = list(chain(*[c.collected_inputs for c in input_collectors]))
    # print('\n'.join([repr(d) for d in input_data]))
    input_processor.input_data = chain(*[c.collected_inputs for c in input_collectors])
    # input_processor.input_data = input_data

    input_processor.process()

    input_processor.commit()

    print("commitment", input_processor.commitment)
    MerkleTreeInputProcessor.print_tree(input_processor.commitment)

    print("Merkle Root", input_processor.processed_data)

    print("{:=^80}".format(" COMPUTING "))

    computation.input_data = input_processor.processed_data

    computation.compute()

    print("OUTPUT", computation.output)


if __name__ == "__main__":
    while True:
        main()
