## what is difference between tuple and set

> tuple (1,2,3): can have duplicate
meanwhile
> set {1,2,3}: cant have duplicate

what does it mean by this code 

```
unique_topics = set([t for t in topics if t != -1])

if t are not -1 so put it in set of unique topics


```

## what make this whole pipeline

> The simple story is like this first we generate the embedding using our xlmr as 1024 dimensions
> and then HDBSCAN: group the embedding to smaller dimension
> and then after it we give it to CTF IDF to give the name of that cluster
> then we return the topics and probabilities of each message

## but why still failing ??

```
# our current approach taking messages as one unique field if the field unique
messages = list(messages_qs.values_list(field_name, flat=True))

#what does it mean by flat=True
means we return values like ['a', 'b', 'c']
instead of [('a',)('b',)]

noted that flat=True only valid when returning one value


so it become cleaner approach

but still problem because we depends on field name to say that it was unique

so our approach was to use id binding with field name to make it unique 

pairs = list(messages_qs.values_list("id", field_name))

# then we pass it to our train_topics method

result = train_topics(
    messages=pairs,
    min_topic_size=min_topic_size,
)


# why value_list ??: means that only returning those columns from the database, not full objects.

messages = Message.objects.all() # to take all values in those objects

messages = list(Message.objects.values_list("id", field_name))

```

## WHAT WILL PROFESSIONAL DO TO TEST SOME FUNCTION OR SETUP ?? BEFORE ACTUALLY IMPLEMENT IT ON FULL PRODUCTION CODE?? ALWAYS TEST IT USING PYTHON SHELL !!

example ??

```bash
python manage.py shell -c "
from chat_analyzer.services.topic_modeler import get_topic_modeler
m = get_topic_modeler
m.preprocess_message([(1, 'tidur'), (2,'makan nasi')])
"

```

## when to use enumerate ??
> when we need to creating some fake indexing


##

```python
text_to_ids = {
    "Hello": [1, 2, 3],      # key = text (str), value = list of IDs
    "World": [4, 5],
    "Hi":    [6],
}

than how do we preprocess if text_to_ids in dictionary ?? also have keys right ??

here is the magic

we sending out our key from those text_to_ids dict, but how ??

texts = self.preprocess_messages(list(text_to_ids.keys()))

    .keys() means we only send keys which is the word


    all_ids = [cid for ids in (text_to_ids).values() for cid in ids]

    # this stay that first we say ok cid is for ids in text_to_ids.values()
# and then we put it all into list of ids for all cid in ids make it list of ids
    conv_map = {c.id: c for c in Conversation.objects.in_bulk(all_ids)}
    # take all the ids of conversation make it into dicstionary

unmapped_ids = set(all_ids)

# we unmapped by putting it into set



```

### the differences between list and tuple

#### LIST [1,2,3]
- can change
- speed slower
- memory more
- methods - bnyk append remove etc
- use case when data change

#### TUPLE (1,2,3)
- cant change
- faster
- less
- method few (count, index only)
- when data is fixed we use tuple
- Fast

#### SET {1,2,3}
- No duplicates
- Unordered
- Mutable
- Super fast 


##### mutability

```python
""" LIST just like what we do in MATLAB"""
mylist = []
mylist = [1,2,3]
mylist.append(4) # add to end
mylist.pop() # remove from end
mylist.insert(0, 0) # insert at position
mylist.remove(2)
mylist.sort() # sort in place
mylist.extend([5, 6]) # add multiple time
mylist.clear() # remove all
len(mylist)

""" TUPLE """
mytuple = ()
mytuple = (1,2,3)
mytuple.count(2) # how many 2 appears
mytuple.index(3) 
mytuple = (42, ) # must have comma

""" SET - UNORDERED, CHANGEABLE, NO DUPLICATES """
# empty set (can't use {} - that's a dict)
myset = set()

numbers = {1,2,3}

myset = set([1,1,2,3,3])

# common operation
numbers = {1, 2, 3}

# Add
numbers.add(4)            # → {1, 2, 3, 4}

# Remove
numbers.remove(2)         # ❌ Error if not found
numbers.discard(2)        # ✅ Safe, no error if not found
numbers.pop()             # remove random item
numbers.clear()           # remove all

# Check
3 in numbers              # → True
len(numbers)             # → length

# with math much more useful
A = {1,2,3,4}
B = {3,4,5,6}

# union (combine)
A | B
A.union(B)

A & B
A.intersection(B)

A - B # what have in A not have in B
A.difference(B)

A ^ B # the difference of both -> {1,2,5,6}

person = {"name": "Alice", "age": 25, "city": "NYC"}

person.keys()    # → dict_keys(["name", "age", "city"])
person.values()  # → dict_values(["Alice", 25, "NYC"])
person.items()   # → dict_items([("name", "Alice"), ("age", 25), ("city", "NYC")])

4. DICT — Key-Value pairs, changeable, NO duplicate keys
Create
# Empty dict
my_dict = {}
my_dict = dict()

# With items
person = {
    "name": "Alice",
    "age": 25,
    "city": "NYC"
}

# From pairs
person = dict([("name", "Alice"), ("age", 25)])
Common operations
person = {"name": "Alice", "age": 25}

# Access
person["name"]              # → "Alice"
person.get("name")          # → "Alice"
person.get("phone", "N/A") # → "N/A" (safe, no error if missing)
person["phone"]             # ❌ KeyError if missing!

# Add / Update
person["email"] = "alice@mail.com"   # add new
person["age"] = 26                    # update existing

# Remove
person.pop("email")         # remove and return value
del person["age"]           # remove by key
person.clear()              # remove all

# Check
"name" in person           # → True (checks KEYS only!)
len(person)                # → number of keys



"""THE VERDICT"""
~ use list when data changes overtime, use tuple when u dont wanna add remove data without accidentally add or remove days


```
