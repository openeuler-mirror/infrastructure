# FAQs

## What if I missed the confirmation email in one specific list?
Assume I `tommylikehu@gmai.com` missed the confirmation email in list `community@openeuler.org`, the steps would be:
1. find someone who have admin privilege to mailman resources in the community, now they are (@freesky-edward or @TommyLike).
2. provide the email address and mail list name.
Usually the confirmation email would expire in 3 days, but there **MUST** be an issue on that setting, therefore we have to
fix it via mailman shell by:

    a. login to mailman core node(pod).

    b. login to mail list shell
    
    ```
    mailman shell -l community@openeuler.org:    
    ```    
    
    c. list all pending emails:
    
    ```bash
    util = getUtility(IPendings)
    list(util.find(mlist=m,pend_type='subscription'))
    ```
    d. find out the user's confirmation token by searching the email address, usually the list item would in the format of:
    ```bash
    ('hex_token'), {'token_owner': 'subscriber', 'email':
    'user@example.com', 'display_name': 'Jane User', 'when':
    '2019-04-09T01:26:08', 'type': 'subscription', 'list_id': 'your.list.id'})
    ```
    e. confirm, commit and quit:
    ```bash
    util.confirm('hex_token')
    commit() 
    ```
Now we can re-subscribe the mail list on website again.


