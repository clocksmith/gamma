"""Hack2Hire 69334452e8ebbb1c53caf2c4 (Design Article System) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

from bisect import bisect_left, insort


class ArticleSystem:
    def __init__(self):
        self.names = [None]
        self.score = [0]
        self.order = []
        self.votes = {}
        self.flips = {}

    def addArticle(self, articleName):
        self.names.append(articleName)
        self.score.append(0)
        article = len(self.names) - 1
        insort(self.order, (0, article))
        return article

    def _vote(self, article, user, new):
        old = self.votes.get((user, article), 0)
        if old == new:
            return
        self.votes[(user, article)] = new
        del self.order[bisect_left(self.order, (-self.score[article], article))]
        self.score[article] += new - old
        insort(self.order, (-self.score[article], article))
        if old == -new:
            recent = self.flips.setdefault(user, {})
            recent.pop(article, None)
            recent[article] = True

    def upvoteArticle(self, articleId, userId):
        self._vote(articleId, userId, 1)

    def downvoteArticle(self, articleId, userId):
        self._vote(articleId, userId, -1)

    def getRecentFlips(self, userId, k):
        result = []
        for article in reversed(self.flips.get(userId, {})):
            if len(result) == k:
                break
            result.append(self.names[article])
        return result

    def getTopArticles(self, k):
        return [self.names[article] for _, article in self.order[:k]]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'ArticleSystem' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = ArticleSystem(*argument_lists[0])
    allowed = {'addArticle', 'upvoteArticle', 'downvoteArticle', 'getRecentFlips', 'getTopArticles'}
    voids = {'upvoteArticle', 'downvoteArticle'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
