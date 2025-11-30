# From geeksforgeeks: https://www.geeksforgeeks.org/dsa/introduction-to-disjoint-set-data-structure-or-union-find-algorithm/

class UnionFind:
    def __init__(self, size):
      
        # Initialize the parent array with each 
        # element as its own representative
        self.parent = list(range(size))
    
    def find(self, i):
      
        # If i itself is root or representative
        if self.parent[i] == i:
            return i
          
        # Else recursively find the representative 
        # of the parent
        return self.find(self.parent[i])
    
    def unite(self, i, j):
      
        # Representative of set containing i
        irep = self.find(i)
        
        # Representative of set containing j
        jrep = self.find(j)
        
        # Make the representative of i's set
        # be the representative of j's set
        self.parent[irep] = jrep
        
