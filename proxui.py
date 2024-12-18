import streamlit as st
import streamlit_authenticator as stauth
from proxapp import PVE
import yaml
from yaml.loader import SafeLoader


def get_session_2proxmox():
    with st.spinner("Connecting..."):
        if session := PVE():
            st.session_state["session"] = session


def show_all_menu():
    col1, col2 = st.columns([0.5, 0.5])

    with col1:
        st.subheader("Start/Stop All VMs")
        button1 = st.button(
            "Start All",
            key="start_all",
            on_click=get_session_2proxmox,
            type="secondary",
            use_container_width=True,
        )
        button2 = st.button(
            "Stop All",
            key="stop_all",
            on_click=get_session_2proxmox,
            type="secondary",
            use_container_width=True,
        )
        button3 = st.button(
            "Delete All",
            key="delete_all",
            on_click=get_session_2proxmox,
            type="primary",
            use_container_width=True,
        )
        # starting VMs
        if (
            all(key in st.session_state.keys() for key in ("session",))
            and button1
        ):
            start_vms()

        # stoping VMs
        if (
            all(key in st.session_state.keys() for key in ("session",))
            and button2
        ):
            stop_vms()

        # Delete VMs
        if (
            all(key in st.session_state.keys() for key in ("session",))
            and button3
        ):
            delete_vms()

    with col2:
        st.subheader("Clone VMs")
        with st.form("clone_vm"):
            clone_vms = st.slider(
                "How many Clone Vms does it create? ",
                min_value=1,
                max_value=10,
                value=1,
                step=1,
            )
            submit = st.form_submit_button(
                "Submit", on_click=get_session_2proxmox
            )

        # check all keys are exist
        if (
            all(key in st.session_state.keys() for key in ("session",))
            and submit
        ):
            clone_vm(clone_vms)


def clone_vm(number):
    print(f"Clonning {number} VMs...")
    session = st.session_state["session"]
    session.create_clone(num=number)


def start_vms():
    session = st.session_state["session"]
    session.action_vms("start")


def stop_vms():
    session = st.session_state["session"]
    session.action_vms("stop")


def delete_vms():
    session = st.session_state["session"]
    session.action_vms("delete")


if __name__ == "__main__":
    # Open YAML file
    with open("config.yaml") as file:
        config = yaml.load(file, Loader=SafeLoader)

    st.set_page_config("proxmox-ve APP", layout="centered")
    # Create authenticator object
    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
        auto_hash=False,
    )

    # Render the login widget
    authenticator.login("sidebar", 5, 5, captcha=False, key="login1")

    # hasehd_pwd = stauth.Hasher([]).generate()
    # st.write(hasehd_pwd)

    # Authenticate users
    if st.session_state["authentication_status"] is False:
        st.error("Username/password is incorrect")
    elif st.session_state["authentication_status"] is None:
        st.warning("Please enter your username and password")
    elif st.session_state["authentication_status"]:
        with st.sidebar:
            authenticator.logout()
            st.write(f'# Welcome *{st.session_state["name"]}*')
            "Proxmox-VE 는 다음 기능들을 제공 합니다."
            " - Template 기반 VM 복사"
            " - 모든 VM 시작/정지 (필수 VM 은 제외)"
            " - 모든 VM 삭제 (필수 VM 은 제외)"
            " - Blacklist 관리 (VM name or ID)"
            " - 새로운 VM 생성"
            "[View the source code](https://github.com/kubeops2/lb2/blob/main/proxmox-ve/proxmox_ui.py)"

        st.title("Proxmox-VE APP")
        show_all_menu()
        # st.write(st.session_state)
        with st.expander("Current VMs"):
            with st.spinner("Connecting..."):
                get_session_2proxmox()
                session = st.session_state["session"]
                vmids = session.status_vm()
                for i in vmids:
                    st.write(i)
            st.button("Reload")
