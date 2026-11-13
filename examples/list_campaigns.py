"""List every campaign in the workspace. Needs AYINBOX_API_KEY with READ_CAMPAIGNS."""

from ayinbox import AyInbox


def main() -> None:
    with AyInbox() as client:
        me = client.me.get()
        print(f"Signed in as {me.get('email')} ({me.get('organization_name', 'no workspace')})")
        for campaign in client.campaigns.list(limit=50):
            print(f"{campaign['id']}  {campaign.get('status', ''):<22}  {campaign.get('name', '')}")


if __name__ == "__main__":
    main()
