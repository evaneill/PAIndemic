﻿using System.Collections;
using UnityEngine;
using UnityEngine.EventSystems;

public class ClickActions : MonoBehaviour
{
    private ArrayList myActions = new ArrayList();
    private ArrayList myActionsURLs = new ArrayList();
    [SerializeField]
    private GameObject myGlow = null;

    // Start is called before the first frame update
    void Start()
    {
        myGlow.SetActive(false);
    }

    public void ResetActions()
    {
        if (myActions.Count > 0)
        {
            myActions.Clear();
            myActionsURLs.Clear();
            myGlow.SetActive(false);
        }
    }

    public void AddAction(string action,string url)
    {
        if (myActions.Count == 0)
        {
            myGlow.SetActive(true);
        }
        myActions.Add(action);
        myActionsURLs.Add(url);
    }

    void OnMouseDown()
    {
        if (myActions.Count > 0)
        {
            PointerEventData pe = new PointerEventData(EventSystem.current);
            pe.position = Input.mousePosition;
            System.Collections.Generic.List<RaycastResult> hits = new System.Collections.Generic.List<RaycastResult>();
            EventSystem.current.RaycastAll(pe, hits);
            foreach (RaycastResult h in hits)
            {
                if (h.gameObject.name.StartsWith("ActionButton"))
                {
                    return;
                }
            }
            GameManager.Focus(this.transform.gameObject, myActions, myActionsURLs);
        }
        else
        {
            if (EventSystem.current.IsPointerOverGameObject())
            {
                return;
            }
            GameManager.LoseFocus();
        }
    }
}
