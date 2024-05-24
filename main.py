import os
from collections import deque

class FSM:
    def __init__(self, states, alphabet, output_alphabet, transitions, start_state):
        self.states = states  
        self.alphabet = alphabet  
        self.output_alphabet = output_alphabet 
        self.transitions = transitions 
        self.start_state = start_state  

    def is_deterministic(self):
        seen_transitions = set()
        for transition in self.transitions:
            key = (transition[0], transition[1])
            if key in seen_transitions:
                return False 
            seen_transitions.add(key)
        return True

    def print_info(self):
        print("FSM Information:")
        print("States:", self.states)
        print("Input Alphabet:", self.alphabet)
        print("Output Alphabet:", self.output_alphabet)
        print("Deterministic:", "Yes" if self.is_deterministic() else "No")
        print("Transitions:")
        for transition in self.transitions:
            print(f"  {transition[0]} --({transition[1]}/{transition[2]})--> {transition[3]}")

def extract_info(transitions):
    states = set()
    alphabet = set()
    output_alphabet = set()

    for i in transitions:
        states.add(i[0])
        states.add(i[3])
        alphabet.add(i[1])
        output_alphabet.add(i[2])

    return list(states), list(alphabet), list(output_alphabet)

def read_FSM_from_file(file_path):
    with open(file_path, 'r') as file:
        content = file.readlines()

    fsms = []
    current_transitions = []

    for line in content: 
        line = line.strip()
        if line.startswith('F'):
            if current_transitions:
                states, alphabet, output_alphabet = extract_info(current_transitions)
                fsm = FSM(states=states, alphabet=alphabet, output_alphabet=output_alphabet, transitions=current_transitions, start_state=start_states)
                fsms.append(fsm)
            current_transitions = []
            start_states = None
        elif line.startswith('n0'):
            start_states = line.split(' ')[1]
        elif line.startswith(('s ', 'i ', 'o ','p ')):
            continue 
        elif line:
            transition = tuple(line.split(' '))
            current_transitions.append(transition)

    if current_transitions: 
        states, alphabet, output_alphabet = extract_info(current_transitions)
        fsm = FSM(states=states, alphabet=alphabet, output_alphabet=output_alphabet, transitions=current_transitions, start_state=start_states)
        fsms.append(fsm)

    return fsms

def intersection_fsm(specification_fsm, implementation_fsm):
    if specification_fsm.alphabet != implementation_fsm.alphabet:
        return None  

    new_states = set()
    new_transitions = []
    output_alphabet = set(specification_fsm.output_alphabet).union(set(implementation_fsm.output_alphabet))
    alphabet = specification_fsm.alphabet
    
    def transition_exist(fsm, state, symbol, output):
        for transition in fsm.transitions:
            if transition[:3] == (state, symbol, output):
                return transition[3]
        return None

    def intersect(spec_state, impl_state):
        nonlocal new_states, new_transitions 

        for symbol in alphabet:
            for output in output_alphabet:
                new_spec_state = transition_exist(specification_fsm, spec_state, symbol, output)
                new_impl_state = transition_exist(implementation_fsm, impl_state, symbol, output)
                if new_spec_state and new_impl_state is not None:
                    new_state = (spec_state, impl_state)    
                    next_state = (new_spec_state, new_impl_state)
                    if new_state not in new_states:  
                        new_states.add(new_state) 
                    if next_state not in new_states:  
                        new_states.add(next_state) 
                    if (new_state, symbol, output, next_state) not in new_transitions:
                        new_transitions.append((new_state, symbol, output, next_state))  
                        intersect(new_spec_state, new_impl_state)

    intersect(specification_fsm.start_state, implementation_fsm.start_state)  
   
    return FSM(states=new_states, alphabet=alphabet, output_alphabet=output_alphabet, transitions=new_transitions, start_state=(specification_fsm.start_state, implementation_fsm.start_state))

def find_seq(fsm):

    def state_transitions(state):
        transitions = []
        for transition in fsm.transitions:
            if transition[0] == (state):
                transitions.append(transition)
        return transitions

    def indeterminate_state(transitions):
        symbols = []
        for transition in transitions:
            symbols.append(transition[1])

        tmp = []
        for symbol in fsm.alphabet:
            if symbol not in symbols:
                tmp.append(symbol)

        if tmp:
            return tmp
        else:
            return None

    def shortest_path(target_state):
        visited = set()
        queue = deque([(fsm.start_state, '')])
        reached_states = set()

        while queue:
            current_state, path = queue.popleft()

            if current_state == target_state:
                reached_states.add(path)
                continue  

            visited.add(current_state)  

            transitions = state_transitions(current_state)

            for transition in transitions:
                next_state, symbol = transition[3], transition[1]
                if next_state not in visited:
                    new_path = path + symbol
                    queue.append((next_state, new_path))
                    
        return reached_states

    list_seq = set()
    indeterminate_states = set()

    for transition in fsm.transitions:
        transitions = state_transitions(transition[3])
        flag = indeterminate_state(transitions)
        if flag:
            paths = shortest_path(transition[3])
            for path in paths:
                for i in flag:
                    list_seq.add(path + i)
            indeterminate_states.add(transition[3])

    seq_states_dict = {}

    for sequence in list_seq:
        seq = sequence[:-1]
        current_states = {fsm.start_state}

        for symbol in seq:
            next_states = set()
            for state in current_states:
                for transition in fsm.transitions:
                    if transition[0] == state and transition[1] == symbol:
                        next_states.add(transition[3])
            if not next_states:
                break
            current_states = next_states

        seq_states_dict[sequence] = current_states

    valid_sequences = set()
    min_length_sequences = set()
    min_length = 10000

    for sequence, states in seq_states_dict.items():
        flag = True
        for state in states:
            if state not in indeterminate_states:
                flag = False
        if flag:
            valid_sequences.add(sequence)
            min_length = min(min_length, len(sequence))

    for seq in valid_sequences:  
        if len(seq) == min_length:  
            min_length_sequences.add(seq)

    return sorted(min_length_sequences)

def check_seq(fsm, input_sequence):
    paths = []

    def dfs(state, current_path, remaining_sequence):
        if not remaining_sequence:
            paths.append(current_path)
            return
        for transition in fsm.transitions:
            if transition[0] == state and (transition[1] == remaining_sequence[0] or transition[1] == ''):
                next_state = transition[3]
                next_path = current_path + transition[2]
                next_remaining = remaining_sequence[1:] if transition[1] == remaining_sequence[0] else remaining_sequence
                dfs(next_state, next_path, next_remaining)

    dfs(fsm.start_state, '', input_sequence)

    return paths

if __name__ == "__main__":

    specification, implementation = read_FSM_from_file('FSMS.txt')

    intersection = intersection_fsm(specification, implementation)

    distinguishing_sequence = find_seq(test_intersection)
    if distinguishing_sequence:
        print(distinguishing_sequence)
        print(check_seq(specification, distinguishing_sequence[0]))
        print(check_seq(implementation, distinguishing_sequence[0]))
    else:
        print("нет различающей последовательности")
