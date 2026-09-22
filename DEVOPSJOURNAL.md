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


```
