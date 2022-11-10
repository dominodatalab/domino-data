from enum import Enum


class GitProviderName(str, Enum):
    BITBUCKET = "Bitbucket"
    BITBUCKETSERVER = "BitbucketServer"
    GITHUB = "Github"
    GITHUBENTERPRISE = "GithubEnterprise"
    GITLAB = "Gitlab"
    GITLABENTERPRISE = "GitlabEnterprise"
    UNKNOWN = "Unknown"

    def __str__(self) -> str:
        return str(self.value)
