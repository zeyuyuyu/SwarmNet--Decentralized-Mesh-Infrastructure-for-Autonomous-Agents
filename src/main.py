# SwarmNet: Decentralized Mesh Infrastructure for Autonomous Agents

import random
import time

class Agent:
    def __init__(self, id):
        self.id = id
        self.neighbors = []
        self.proposals = []
        self.votes = {}

    def connect(self, other_agent):
        self.neighbors.append(other_agent)
        other_agent.neighbors.append(self)

    def propose(self, proposal):
        self.proposals.append(proposal)
        self.broadcast_proposal(proposal)

    def broadcast_proposal(self, proposal):
        for neighbor in self.neighbors:
            neighbor.receive_proposal(proposal)

    def receive_proposal(self, proposal):
        if proposal not in self.proposals:
            self.proposals.append(proposal)

    def vote(self, proposal, vote):
        self.votes[proposal] = vote
        self.broadcast_vote(proposal, vote)

    def broadcast_vote(self, proposal, vote):
        for neighbor in self.neighbors:
            neighbor.receive_vote(proposal, vote)

    def receive_vote(self, proposal, vote):
        if proposal in self.proposals:
            self.votes[proposal] = vote

    def tally_votes(self, proposal):
        yes_votes = 0
        no_votes = 0
        for vote in self.votes.values():
            if vote:
                yes_votes += 1
            else:
                no_votes += 1
        return yes_votes > no_votes

    def finalize_proposal(self, proposal):
        if self.tally_votes(proposal):
            print(f"Proposal '{proposal}' accepted!")
        else:
            print(f"Proposal '{proposal}' rejected.")
        self.proposals.remove(proposal)
        self.votes = {}

def main():
    agents = [Agent(i) for i in range(10)]
    for i in range(len(agents)):
        for j in range(i+1, len(agents)):
            agents[i].connect(agents[j])

    while True:
        agent = random.choice(agents)
        proposal = f"Proposal {len(agent.proposals) + 1}"
        agent.propose(proposal)

        for _ in range(3):
            for a in agents:
                a.vote(proposal, random.choice([True, False]))
            time.sleep(1)

        agent.finalize_proposal(proposal)

if __name__ == "__main__":
    main()
